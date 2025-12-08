import json
import logging
import os
import re
import time
import traceback

import jieba
import jieba.analyse
import numpy as np
import requests
from openai import OpenAI
from requests.adapters import HTTPAdapter
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from urllib3.util.retry import Retry

# 直接使用固定的API密钥（与chat_system.py保持一致）
OPENAI_API_KEY = "sk-59a6a7690bfb42cd887365795e114002"
OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# Ollama API配置
OLLAMA_BASE_URL = "http://localhost:11434/api"
OLLAMA_MODEL = "qwen3:8b"  # 默认使用qwen2.5:7b模型，可以根据需要更改

# Ollama请求配置
OLLAMA_REQUEST_TIMEOUT = 180  # 请求超时时间（秒）
OLLAMA_MAX_RETRIES = 3  # 最大重试次数
OLLAMA_RETRY_BACKOFF = 1.5  # 重试间隔倍数
OLLAMA_MAX_WORKERS = 2  # 并发处理的最大工作线程数


# 创建带有重试机制的会话
def create_retry_session(
    retries=OLLAMA_MAX_RETRIES, backoff_factor=OLLAMA_RETRY_BACKOFF, status_forcelist=[408, 429, 500, 502, 503, 504]
):
    """创建带有重试机制的请求会话"""
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def check_ollama_service():
    """检查Ollama服务是否可用"""
    logger = logging.getLogger(__name__)
    try:
        # 使用带重试机制的会话，但设置较短的超时时间和较少的重试次数
        session = create_retry_session(retries=1, backoff_factor=0.5)
        response = session.get(f"{OLLAMA_BASE_URL}/tags", timeout=10)
        if response.status_code == 200:
            logger.info("Ollama服务正在运行")
            return True
        else:
            logger.warning(f"Ollama服务返回错误状态码: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"无法连接到Ollama服务: {str(e)}")
        return False


def is_ollama_available():
    """检查Ollama服务是否可用"""
    return check_ollama_service()


def process_long_video_subtitles(subtitles):
    """分块处理长视频字幕，使用优化的并发和重试机制"""
    logger = logging.getLogger(__name__)
    logger.info("开始分块处理长视频字幕")

    # 根据字幕总数动态确定分块大小
    total_subtitles = len(subtitles)
    if total_subtitles < 200:
        chunk_size = 80  # 较小的块，适合短视频
    elif total_subtitles < 500:
        chunk_size = 120  # 中等大小的块，适合中等长度视频
    else:
        chunk_size = 150  # 较大的块，适合长视频

    # 存储所有处理结果
    all_results = []

    # 导入并行处理模块
    import concurrent.futures

    # 使用并发队列来控制并发数量
    from queue import Queue

    task_queue = Queue()

    # 将字幕分块并添加到任务队列
    chunks = []
    for i in range(0, len(subtitles), chunk_size):
        end_idx = min(i + chunk_size, len(subtitles))
        chunk = subtitles[i:end_idx]
        chunks.append((i, end_idx - 1, chunk))

    # 根据字幕块数量动态调整并发线程数
    num_chunks = len(chunks)
    max_workers = min(OLLAMA_MAX_WORKERS, num_chunks)  # 不超过块数

    logger.info(f"共{num_chunks}个字幕块，使用{max_workers}个并发线程处理")

    # 定义处理单个字幕块的函数，包含重试机制
    def process_chunk_with_retry(start_idx, end_idx, chunk, max_retries=OLLAMA_MAX_RETRIES):
        chunk_desc = f"{start_idx}-{end_idx}"
        logger.info(f"开始处理字幕块 {chunk_desc}，共{len(chunk)}条字幕")

        retries = 0
        while retries <= max_retries:
            try:
                # 在重试前添加随机延迟，避免并发请求对服务器的压力
                if retries > 0:
                    # 指数退避策略，每次重试等待时间增加
                    wait_time = OLLAMA_RETRY_BACKOFF**retries
                    logger.info(f"字幕块 {chunk_desc} 第{retries}次重试，等待{wait_time:.2f}秒")
                    time.sleep(wait_time)

                # 处理字幕块
                result = merge_subtitles_by_semantics_ollama(chunk)

                if result:
                    # 调整每个段落的索引以反映其在原始字幕中的位置
                    for segment in result:
                        if 'original_indices' in segment:
                            # 将块内索引转换为全局索引
                            segment['original_indices'] = [idx + start_idx for idx in segment['original_indices']]

                    logger.info(f"字幕块 {chunk_desc} 处理成功，生成了 {len(result)} 个段落")
                    return result
                else:
                    logger.warning(f"字幕块 {chunk_desc} 处理结果为空，尝试重试")
                    retries += 1
            except Exception as e:
                logger.error(f"字幕块 {chunk_desc} 处理失败: {str(e)}")
                retries += 1
                if retries > max_retries:
                    logger.error(f"字幕块 {chunk_desc} 超过最大重试次数，将使用备用方法")
                    # 如果超过最大重试次数，尝试使用备用方法
                    try:
                        logger.info(f"字幕块 {chunk_desc} 尝试使用备用方法")
                        return merge_subtitles_by_semantics(chunk)
                    except Exception as backup_e:
                        logger.error(f"字幕块 {chunk_desc} 备用方法也失败: {str(backup_e)}")
                        return None

        # 如果所有重试都失败，返回None
        return None

    # 使用线程池并行处理字幕块
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 准备任务列表
        future_to_chunk = {}

        # 提交所有任务到线程池
        for i, end_idx, chunk in chunks:
            logger.info(f"提交字幕块 {i}-{end_idx} 到线程池，共{len(chunk)}条字幕")
            future = executor.submit(process_chunk_with_retry, i, end_idx, chunk)
            future_to_chunk[future] = (i, end_idx)

        # 收集结果
        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk_range = future_to_chunk[future]
            try:
                chunk_results = future.result()
                if chunk_results:
                    all_results.extend(chunk_results)
                    logger.info(
                        f"字幕块 {chunk_range[0]}-{chunk_range[1]} 处理完成，生成了 {len(chunk_results)} 个段落"
                    )
                else:
                    logger.warning(f"字幕块 {chunk_range[0]}-{chunk_range[1]} 处理结果为空")
                    backup_results = process_subtitle_chunk_backup(chunk, start_idx)

                    # 调整每个段落的索引以反映其在原始字幕中的位置
                    for segment in backup_results:
                        if 'original_indices' in segment:
                            # 将块内索引转换为全局索引
                            segment['original_indices'] = [idx + start_idx for idx in segment['original_indices']]
                    if backup_results:
                        all_results.extend(backup_results)
                        logger.info(
                            f"字幕块 {chunk_range[0]}-{chunk_range[1]} 使用备用方法处理完成，生成了 {len(backup_results)} 个段落"
                        )
            except Exception as e:
                logger.error(f"处理字幕块 {chunk_range[0]}-{chunk_range[1]} 时出错: {str(e)}")
                logger.error(traceback.format_exc())

                # 当处理出错时，使用备用方法处理该块
                try:
                    start_idx = chunk_range[0]
                    end_idx = chunk_range[1] + 1  # 范围是闭区间
                    chunk = subtitles[start_idx:end_idx]
                    backup_results = process_subtitle_chunk_backup(chunk, start_idx)
                    if backup_results:
                        all_results.extend(backup_results)
                        logger.info(
                            f"字幕块 {chunk_range[0]}-{chunk_range[1]} 使用备用方法处理完成，生成了 {len(backup_results)} 个段落"
                        )
                except Exception as backup_error:
                    logger.error(f"备用方法处理字幕块 {chunk_range[0]}-{chunk_range[1]} 也失败: {str(backup_error)}")

    # 按照开始时间排序结果
    all_results.sort(key=lambda x: x["start_time"])

    logger.info(f"长视频分块处理完成，共生成{len(all_results)}个语义段落")
    return all_results


def process_subtitle_chunk_backup(chunk, start_offset):
    """备用方法处理单个字幕块，使用更简单的方式确保不会失败"""
    logger = logging.getLogger(__name__)
    logger.info(f"使用备用方法处理字幕块，共{len(chunk)}条字幕")

    try:
        # 使用更简单的分段策略，按固定数量分段
        chunk_size = len(chunk)

        # 根据块大小确定段落数，与主处理方法保持一致
        if chunk_size < 20:
            num_segments = 3  # 2-3个段落，取中间值
        elif chunk_size < 50:
            num_segments = 5  # 4-6个段落，取中间值
        elif chunk_size < 100:
            num_segments = 10  # 10-11个段落，取中间值
        elif chunk_size < 150:
            num_segments = 15  # 15-16个段落，取中间值
        else:
            num_segments = 20  # 20-21个段落，取中间值

        # 计算每个段落包含的字幕数量
        subtitles_per_segment = max(1, chunk_size // num_segments)

        # 存储结果
        results = []

        # 按固定间隔分段
        for i in range(0, chunk_size, subtitles_per_segment):
            end_idx = min(i + subtitles_per_segment - 1, chunk_size - 1)

            # 收集该段落内的所有原始字幕
            original_subtitles_texts = [chunk[j]["text"] for j in range(i, end_idx + 1)]
            # 合并文本，确保包含所有内容
            segment_text = " ".join(original_subtitles_texts)

            # 格式化文本，提高可读性
            formatted_text = segment_text
            try:
                # 处理中文句号、问号、感叹号和英文句号、问号、感叹号
                formatted_text = re.sub(r'([。！？.!?])\s*', r'\1\n\n', formatted_text)

                # 处理逗号和分号，添加适当的空格
                formatted_text = re.sub(r'([，,、;；:：])\s*', r'\1 ', formatted_text)

                # 确保每个句子都在新行开始
                formatted_text = re.sub(r'\n([^\n])', r'\n\n\1', formatted_text)

                # 处理连续的换行符，避免过多空行
                formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)

                # 合并连续的空格
                formatted_text = re.sub(r'\s{2,}', ' ', formatted_text)
            except Exception as e:
                logger.warning(f"格式化文本出错: {str(e)}")

            # 生成简单标题
            try:
                # 尝试使用传统方法生成标题
                title = generate_title_traditional(segment_text)
            except Exception as e:
                logger.warning(f"生成标题出错: {str(e)}")
                # 使用默认标题
                title = f"第{len(results)+1}部分"

            # 添加结果
            results.append(
                {
                    "start_time": chunk[i]["start_time"],
                    "end_time": chunk[end_idx]["end_time"],
                    "text": formatted_text,
                    "title": title,
                    "original_subtitles": [
                        {
                            "start_time": chunk[j]["start_time"],
                            "end_time": chunk[j]["end_time"],
                            "text": chunk[j]["text"],
                        }
                        for j in range(i, end_idx + 1)
                    ],
                }
            )

        logger.info(f"备用方法处理完成，生成了{len(results)}个段落")
        return results
    except Exception as e:
        logger.error(f"备用方法处理出错: {str(e)}")
        # 最后的保底方案：将整个块作为一个段落返回
        try:
            return [
                {
                    "start_time": chunk[0]["start_time"],
                    "end_time": chunk[-1]["end_time"],
                    "text": " ".join([sub["text"] for sub in chunk]),
                    "title": "字幕内容",
                    "original_subtitles": [
                        {"start_time": sub["start_time"], "end_time": sub["end_time"], "text": sub["text"]}
                        for sub in chunk
                    ],
                }
            ]
        except Exception as final_error:
            logger.error(f"最终保底方案也失败: {str(final_error)}")
            return []


def process_subtitle_chunk(chunk, start_offset):
    """处理单个字幕块"""
    logger = logging.getLogger(__name__)
    # 提取字幕文本
    chunk_text = ""
    for i, subtitle in enumerate(chunk):
        chunk_text += f"{i+1}. {subtitle['text']}\n"

    # 根据字幕块大小动态确定分段策略，与不分块处理时的标准保持一致
    chunk_size = len(chunk)
    if chunk_size < 20:  # 字幕很少
        segment_guidance = "应该生成2-3个段落，不要过度分段"
        segment_count = "2-3"
    elif chunk_size < 50:  # 字幕较少
        segment_guidance = "应该生成4-6个段落，确保每个段落内容连贯"
        segment_count = "4-6"
    elif chunk_size < 100:  # 字幕中等
        segment_guidance = "应该生成10-11个段落，合理划分主题"
        segment_count = "10-11"
    elif chunk_size < 150:  # 字幕较多
        segment_guidance = "应该生成15-16个段落，确保主题清晰划分"
        segment_count = "15-16"
    else:  # 字幕很多
        segment_guidance = "应该生成20-21个段落，确保主题清晰划分"
        segment_count = "20-21"

    # 构建提示词 - 根据字幕块大小动态调整分段要求
    prompt_template = """请分析以下字幕文本，按语义将其分成若干段落，并为每个段落生成标题。

{{ text }}

要求：
1. 根据字幕总数（共{{ chunk_size }}条），{{ segment_guidance }}
2. 基于语义内容进行分段，相关主题应该在同一段落中
3. 确保每个段落的开始和结束索引正确
4. 为每个段落生成一个简短的标题（不超过8个字符）

返回格式（JSON）：
```
[
  {{
    "start_index": 0,
    "end_index": 30,
    "formatted_text": "这是第一个语义段落的内容。包含多个相关主题。",
    "title": "主题介绍"
  }},
  {{
    "start_index": 31,
    "end_index": 60,
    "formatted_text": "这是第二个语义段落的内容。包含另一组相关主题。",
    "title": "要点讨论"
  }}
]
```

请直接返回JSON格式的结果，不要有任何解释或其他内容。注意：必须将全部内容合并为{{ segment_count }}个段落，不要生成过多段落。"""
    # 替换所有变量
    prompt = prompt_template.replace("{{ text }}", chunk_text)
    prompt = prompt.replace("{{ chunk_size }}", str(chunk_size))
    prompt = prompt.replace("{{ segment_guidance }}", segment_guidance)
    prompt = prompt.replace("{{ segment_count }}", segment_count)

    # 调用Ollama API
    try:
        # 检查Ollama服务是否可用
        if not is_ollama_available():
            logger.error("Ollama服务不可用")
            raise Exception("Ollama服务不可用")

        # 直接使用测试过的API地址格式
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # 降低温度以加快生成速度
                        "num_predict": 2048,  # 增加生成的token数量上限
                        "num_ctx": 4096,  # 增加上下文窗口大小
                    },
                },
                timeout=120,  # 增加超时时间到120秒
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API请求失败: {str(e)}")
            raise Exception(f"Ollama API请求失败: {str(e)}")

        # 提取JSON部分
        result = response.json()
        json_str = result.get("response", "")

        # 提取JSON字符串（如果包含在```中）
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        # 确保JSON字符串是完整的
        json_str = re.sub(r'[^}\]]*$', '', json_str)

        # 解析JSON
        try:
            segments_info = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"无法解析JSON响应: {json_str}")

            # 尝试修复常见的JSON格式错误
            fixed_json = _fix_json_format(json_str)
            segments_info = json.loads(fixed_json)

        # 处理结果
        results = []

        # 确定目标段落数量
        target_segment_count = 0
        if chunk_size < 20:  # 字幕很少
            target_segment_count = 3  # 2-3个段落，取中间值
        elif chunk_size < 50:  # 字幕较少
            target_segment_count = 5  # 4-6个段落，取中间值
        elif chunk_size < 100:  # 字幕中等
            target_segment_count = 10  # 10-11个段落，取中间值
        elif chunk_size < 150:  # 字幕较多
            target_segment_count = 15  # 15-16个段落，取中间值
        else:  # 字幕很多
            target_segment_count = 20  # 20-21个段落，取中间值

        # 检查LLM生成的段落数量是否符合要求
        if len(segments_info) < target_segment_count * 0.7 or len(segments_info) > target_segment_count * 1.3:
            logger.warning(
                f"LLM生成的段落数量({len(segments_info)})与目标数量({target_segment_count})相差过大，使用强制分段"
            )
            # 当LLM生成的段落数量与目标相差过大时，使用强制分段
            return process_subtitle_chunk_backup(chunk, start_offset)

        # 如果LLM生成的段落数量基本符合要求，则正常处理
        for segment in segments_info:
            # 获取段落的起始和结束索引（相对于当前块）
            chunk_start_index = segment.get("start_index", 0)
            chunk_end_index = segment.get("end_index", 0)

            # 确保索引在当前块的有效范围内
            chunk_start_index = max(0, min(chunk_start_index, len(chunk) - 1))
            chunk_end_index = max(chunk_start_index, min(chunk_end_index, len(chunk) - 1))

            # 计算全局索引（相对于整个字幕列表）
            global_start_index = start_offset + chunk_start_index
            global_end_index = start_offset + chunk_end_index

            # 获取格式化文本和标题
            formatted_text = segment.get("formatted_text", "")

            # 移除文本中的索引标记 [0], [1], [2] 等
            if formatted_text:
                formatted_text = re.sub(r'\[\d+\]\s*', '', formatted_text)

            # 始终使用原始字幕内容，确保不会丢失内容
            # 收集该段落内的所有原始字幕
            original_subtitles_texts = [chunk[i]["text"] for i in range(chunk_start_index, chunk_end_index + 1)]

            # 如果没有格式化文本，或者格式化文本明显短于原始文本，使用原始合并文本
            original_text = " ".join(original_subtitles_texts)
            if (
                not formatted_text or len(formatted_text) < len(original_text) * 0.7
            ):  # 如果格式化文本长度小于原始文本的70%
                # 尝试格式化原始文本
                try:
                    # 处理中文句号、问号、感叹号和英文句号、问号、感叹号
                    original_text = re.sub(
                        r'([\u3002\uff01\uff1f.!?])\s*', r'\1\n\n', original_text
                    )  # 双换行增加可读性

                    # 处理逗号和分号，添加适当的空格
                    original_text = re.sub(r'([\uff0c,\u3001;\uff1b:\uff1a])\s*', r'\1 ', original_text)

                    # 确保每个句子都在新行开始
                    original_text = re.sub(r'\n([^\n])', r'\n\n\1', original_text)

                    # 处理连续的换行符，避免过多空行
                    original_text = re.sub(r'\n{3,}', '\n\n', original_text)

                    # 合并连续的空格
                    original_text = re.sub(r'\s{2,}', ' ', original_text)

                    formatted_text = original_text
                except Exception as e:
                    logger.warning(f"格式化原始文本出错: {str(e)}")
                    formatted_text = original_text

            title = segment.get("title", f"段落{len(results)+1}")

            # 获取时间信息
            start_time = chunk[chunk_start_index]["start_time"]
            end_time = chunk[chunk_end_index]["end_time"]

            # 收集该段落的所有原始字幕信息
            original_subtitles = [
                {"start_time": chunk[j]["start_time"], "end_time": chunk[j]["end_time"], "text": chunk[j]["text"]}
                for j in range(chunk_start_index, chunk_end_index + 1)
            ]

            results.append(
                {
                    "start_time": start_time,
                    "end_time": end_time,
                    "text": formatted_text,
                    "title": title,
                    "original_indices": list(range(global_start_index, global_end_index + 1)),
                    "original_subtitles": original_subtitles,
                }
            )

        return results

    except Exception as e:
        logger.error(f"处理字幕块时出错: {str(e)}")
        logger.error(traceback.format_exc())

        # 如果处理失败，直接抛出异常，让上层函数处理
        raise


def merge_subtitles_by_semantics_ollama(subtitles):
    """使用Ollama进行语义分段和标题生成"""
    logger = logging.getLogger(__name__)

    # 如果字幕数量为0，直接返回空列表
    if not subtitles or len(subtitles) == 0:
        logger.warning("字幕数量为0，返回空列表")
        return []

    # 如果字幕数量太少，不进行合并
    if len(subtitles) < 5:
        logger.info(f"字幕数量太少（{len(subtitles)}条），不进行合并")
        for sub in subtitles:
            sub['title'] = sub['text'][:10] + "..." if len(sub['text']) > 10 else sub['text']
        return subtitles

    # 尝试使用Ollama方法
    try:
        # 检查Ollama服务是否可用
        if not check_ollama_service():
            logger.warning("Ollama服务不可用，使用方案二")
            return merge_subtitles_by_semantics(subtitles)

        logger.info("尝试使用Ollama进行语义分段和标题生成（方案一）")

        # 判断是否为长视频（超过150条字幕）
        is_long_video = len(subtitles) > 150

        if is_long_video:
            logger.info(f"检测到长视频（{len(subtitles)}条字幕），采用分块处理")
            try:
                return process_long_video_subtitles(subtitles)
            except Exception as e:
                logger.error(f"长视频处理失败: {str(e)}")
                logger.info("长视频处理失败，使用方案二")
                return merge_subtitles_by_semantics(subtitles)

        # 短视频处理逻辑（原有逻辑）
        # 提取所有字幕文本
        full_text = ""
        for i, sub in enumerate(subtitles):
            full_text += f"[{i}] {sub['text']}\n"

        logger.info(f"提取了{len(subtitles)}条字幕文本")
        # 构建提示词 - 一次性请求分段、添加标点和生成标题
        # 根据字幕总数量确定分段策略
        subtitle_count = len(subtitles)
        if subtitle_count < 20:  # 字幕很少
            segment_guidance = "应该生成2-3个段落，不要过度分段"
        elif subtitle_count < 50:  # 字幕较少
            segment_guidance = "应该生成4-6个段落，确保每个段落内容连贯"
        elif subtitle_count < 100:  # 字幕中等
            segment_guidance = "应该生成10-11个段落，合理划分主题"
        elif subtitle_count < 150:  # 字幕较多
            segment_guidance = "应该生成15-16个段落，确保主题清晰划分"
        elif subtitle_count < 200:  # 字幕很多
            segment_guidance = "应该生成20-21个段落，确保主题清晰划分"
        elif subtitle_count < 300:  # 字幕非常多
            segment_guidance = "应该生成25-26个段落，确保主题清晰划分"
        elif subtitle_count < 400:  # 字幕极多
            segment_guidance = "应该生成30-31个段落，确保主题清晰划分"
        elif subtitle_count < 500:  # 字幕极多
            segment_guidance = "应该生成35-36个段落，确保主题清晰划分"
        elif subtitle_count < 600:  # 字幕极多
            segment_guidance = "应该生成40-41个段落，确保主题清晰划分"
        elif subtitle_count < 700:  # 字幕极多
            segment_guidance = "应该生成45-46个段落，确保主题清晰划分"
        elif subtitle_count < 800:  # 字幕极多
            segment_guidance = "应该生成50-51个段落，确保主题清晰划分"
        elif subtitle_count < 900:  # 字幕极多
            segment_guidance = "应该生成55-56个段落，确保主题清晰划分"
        else:  # 字幕数量巨大
            segment_guidance = "应该生成60-61个段落，确保主题清晰划分"

        prompt_template = """请分析以下视频字幕文本，并完成三个任务：
1. 根据内容的语义连贯性将其分成若干个有意义的段落
2. 为每个段落添加适当的标点符号，使其更易于阅读（注意：返回的文本中不要包含索引标记[0]、[1]等）
3. 为每个段落生成一个简短的标题（不超过10个字）

字幕文本（每行前面的数字是字幕的索引）：
{{ text }}

要求：
1. 根据内容的语义连贯性和主题变化进行分段，而不是简单地按固定间隔分段
2. 每个段落应该表达一个相对完整的意思或主题
3. 返回JSON格式的结果，包含每个段落的开始和结束字幕索引
4. 根据字幕总数（共{{ subtitle_count }}条），{{ segment_guidance }}
5. 确保分段是连续的，不要有重叠或遗漏
6. 返回的文本中不要包含索引标记[0]、[1]等
7. 为每个段落生成一个简短、具体的标题，反映其主要内容

返回格式（JSON）：
```
[
  {
    "start_index": 0,
    "end_index": 5,
    "formatted_text": "这是添加了标点符号的文本。这样更容易阅读和理解。",
    "title": "主题介绍"
  },
  {
    "start_index": 6,
    "end_index": 12,
    "formatted_text": "这是第二段添加了标点符号的文本。包含了完整的标点和语法修正。",
    "title": "要点讨论"
  }
]
```

请直接返回JSON格式的结果，不要有任何解释或其他内容。确保JSON格式正确，每个属性之间都有逗号分隔。"""

        # 使用安全的方式替换变量
        prompt = prompt_template.replace("{{ text }}", full_text)
        prompt = prompt.replace("{{ subtitle_count }}", str(subtitle_count))
        prompt = prompt.replace("{{ segment_guidance }}", segment_guidance)

        # 调用Ollama API - 只调用一次
        logger.info("开始调用Ollama API进行分段、添加标点和生成标题")
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.3}},
                timeout=60,
            )

            if response.status_code != 200:
                logger.error(f"Ollama API调用失败: {response.status_code} {response.text}")
                return merge_subtitles_by_semantics(subtitles)
        except Exception as e:
            logger.error(f"Ollama API请求异常: {str(e)}")
            return merge_subtitles_by_semantics(subtitles)

        # 获取响应文本
        response_text = response.json().get("response", "")

        # 从响应文本中提取JSON部分
        json_match = re.search(r'```\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析整个响应
            json_str = response_text

        # 清理JSON字符串，移除可能的非JSON内容
        json_str = re.sub(r'^[^[{]*', '', json_str)
        json_str = re.sub(r'[^}\]]*$', '', json_str)

        # 解析JSON响应
        try:
            segments_info = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"无法解析JSON响应: {json_str}")

            # 尝试修复常见的JSON格式错误
            fixed_json = _fix_json_format(json_str)
            try:
                segments_info = json.loads(fixed_json)
                logger.info("成功修复并解析JSON响应")
            except:
                logger.error("无法解析Ollama返回的JSON，使用方案二")
                return merge_subtitles_by_semantics(subtitles)

        # 确保segments_info是列表类型
        if not isinstance(segments_info, list):
            logger.error(f"解析的JSON不是列表类型: {segments_info}")
            return merge_subtitles_by_semantics(subtitles)

        # 确定目标段落数量
        target_segments_count = 0
        subtitle_count = len(subtitles)
        if subtitle_count < 20:
            target_segments_count = 3
        elif subtitle_count < 50:
            target_segments_count = 6
        elif subtitle_count < 100:
            target_segments_count = 11
        elif subtitle_count < 150:
            target_segments_count = 16
        elif subtitle_count < 200:
            target_segments_count = 21
        elif subtitle_count < 300:
            target_segments_count = 26
        elif subtitle_count < 400:
            target_segments_count = 31
        elif subtitle_count < 500:
            target_segments_count = 36
        elif subtitle_count < 600:
            target_segments_count = 41
        elif subtitle_count < 700:
            target_segments_count = 46
        elif subtitle_count < 800:
            target_segments_count = 51
        elif subtitle_count < 900:  # 字幕极多
            target_segments_count = 56
        else:  # 字幕数量巨大
            target_segments_count = 61

        # 合并字幕 - 直接使用Ollama返回的标题，但使用原始文本
        merged_subtitles = []
        for segment in segments_info:
            start_index = segment.get("start_index")
            end_index = segment.get("end_index")
            title = segment.get("title", "")

            if start_index is None or end_index is None:
                logger.warning(f"段落信息不完整: {segment}")
                continue

            # 确保索引在有效范围内
            start_index = max(0, min(start_index, len(subtitles) - 1))
            end_index = max(start_index, min(end_index, len(subtitles) - 1))

            # 始终使用原始字幕文本，而不是模型生成的格式化文本
            original_text = " ".join([subtitles[i]["text"] for i in range(start_index, end_index + 1)])

            # 格式化文本，提高可读性
            try:
                # 处理中文句号、问号、感叹号和英文句号、问号、感叹号 - 强制在这些标点后分段
                original_text = re.sub(r'([。！？.!?])\s*', r'\1\n\n', original_text)  # 双换行增加可读性

                # 处理逗号和分号，添加适当的空格
                original_text = re.sub(r'([，,、;；:：])\s*', r'\1 ', original_text)

                # 确保每个句子都在新行开始
                original_text = re.sub(r'\n([^\n])', r'\n\n\1', original_text)

                # 处理连续的换行符，避免过多空行
                original_text = re.sub(r'\n{3,}', '\n\n', original_text)

                # 合并连续的空格
                original_text = re.sub(r'\s{2,}', ' ', original_text)

                # 确保段落之间有足够的空白，但不过度
                original_text = re.sub(r'([^\n])\n([^\n])', r'\1\n\n\2', original_text)
                original_text = re.sub(r'\n\n\n+', '\n\n', original_text)

                logger.info("字幕格式化完成")
            except Exception as e:
                logger.error(f"字幕格式化出错: {str(e)}")
                # 出错时保留原始文本，不进行格式化

            # 使用LLM生成标题
            try:
                # 首先尝试使用Ollama生成标题
                if check_ollama_service():
                    new_title = generate_title_with_ollama(original_text)
                    if new_title and len(new_title.strip()) > 0:
                        title = new_title.strip()
                        logger.info(f"使用Ollama生成标题: {title}")
                # 如果Ollama失败，尝试使用在线LLM
                if not title or title == f"第{len(merged_subtitles) + 1}部分":
                    new_title = generate_title_with_llm(original_text)
                    if new_title and len(new_title.strip()) > 0:
                        title = new_title.strip()
                        logger.info(f"使用在线LLM生成标题: {title}")
            except Exception as e:
                logger.error(f"生成标题时出错: {str(e)}")

            # 如果没有成功生成标题，使用默认标题
            if not title:
                title = f"第{len(merged_subtitles) + 1}部分"

            # 创建合并后的字幕，使用原始文本
            merged_subtitle = {
                "start_time": subtitles[start_index]["start_time"],
                "end_time": subtitles[end_index]["end_time"],
                "text": original_text,
                "title": title,
                "original_indices": list(range(start_index, end_index + 1)),
            }

            merged_subtitles.append(merged_subtitle)

        # 先按照时间戳对所有段落进行排序，确保时间顺序正确
        merged_subtitles = sorted(merged_subtitles, key=lambda x: x["start_time"])
        logger.info("已对所有段落按时间戳进行排序")

        # 检查段落数量是否符合要求
        actual_segments_count = len(merged_subtitles)
        logger.info(f"模型生成的段落数量: {actual_segments_count}, 目标段落数量: {target_segments_count}")

        # 如果没有段落，使用方案二
        if not merged_subtitles:
            logger.warning("Ollama没有返回有效的段落，使用方案二")
            return merge_subtitles_by_semantics(subtitles)

        # 获取目标段落数量范围
        target_min = int(segment_guidance.split("应该生成")[1].split("-")[0])
        target_max = int(segment_guidance.split("-")[1].split("个段落")[0])

        # 如果生成的段落数量不符合预期，进行智能调整
        # 限制标题长度，确保所有标题都不超过8个字符
        for subtitle in merged_subtitles:
            if len(subtitle["title"]) > 8:
                subtitle["title"] = subtitle["title"][:8]

        if len(merged_subtitles) < target_min:
            logger.info(f"生成的段落数量({len(merged_subtitles)})少于目标范围({target_min}-{target_max})，进行智能分割")

            # 智能分割现有段落以达到目标数量
            adjusted_subtitles = []
            segments_to_add = target_min - len(merged_subtitles)

            # 按段落长度排序，优先分割较长的段落
            sorted_by_length = sorted(merged_subtitles, key=lambda x: len(x['text']), reverse=True)

            # 计算需要分割的段落数量
            segments_to_split = min(segments_to_add, len(sorted_by_length))

            # 分割最长的几个段落
            for i, segment in enumerate(merged_subtitles):
                if i < segments_to_split and len(segment['text']) > 100:  # 只分割较长的段落
                    # 获取原始字幕索引
                    original_indices = segment.get('original_indices', [])
                    if not original_indices and 'start_index' in segment and 'end_index' in segment:
                        original_indices = list(range(segment['start_index'], segment['end_index'] + 1))

                    if len(original_indices) >= 4:  # 确保有足够的字幕可以分割
                        # 找到中间位置分割点
                        mid_point = len(original_indices) // 2

                        # 创建两个新段落
                        first_half_indices = original_indices[:mid_point]
                        second_half_indices = original_indices[mid_point:]

                        if first_half_indices and second_half_indices:
                            # 第一部分
                            first_half_text = " ".join([subtitles[idx]["text"] for idx in first_half_indices])

                            # 为第一部分生成新标题
                            # 对分割后的段落内容进行总结生成标题
                            try:
                                # 尝试使用生成标题的函数
                                first_half_title = generate_title_traditional(first_half_text, max_words=4)
                                # 确保标题不为空
                                if not first_half_title or len(first_half_title) < 2:
                                    # 如果生成失败，使用文本的前几个字
                                    words = re.sub(r'[\s\n]+', '', first_half_text[:20])
                                    first_half_title = words[:8]
                            except Exception as e:
                                logger.error(f"生成第一部分标题时出错: {str(e)}")
                                # 出错时使用原标题
                                first_half_title = segment["title"]

                            # 确保标题不超过8个字符
                            if len(first_half_title) > 8:
                                first_half_title = first_half_title[:8]

                            first_half = {
                                "start_time": subtitles[first_half_indices[0]]["start_time"],
                                "end_time": subtitles[first_half_indices[-1]]["end_time"],
                                "text": first_half_text,
                                "title": first_half_title,
                                "original_indices": first_half_indices,
                            }

                            # 第二部分
                            second_half_text = " ".join([subtitles[idx]["text"] for idx in second_half_indices])

                            # 为第二部分生成新标题
                            # 对分割后的段落内容进行总结生成标题
                            try:
                                # 尝试使用生成标题的函数
                                second_half_title = generate_title_traditional(second_half_text, max_words=4)
                                # 确保标题不为空
                                if not second_half_title or len(second_half_title) < 2:
                                    # 如果生成失败，使用文本的前几个字
                                    words = re.sub(r'[\s\n]+', '', second_half_text[:20])
                                    second_half_title = words[:8]
                            except Exception as e:
                                logger.error(f"生成第二部分标题时出错: {str(e)}")
                                # 出错时使用原标题
                                second_half_title = segment["title"]

                            # 确保标题不超过8个字符
                            if len(second_half_title) > 8:
                                second_half_title = second_half_title[:8]

                            second_half = {
                                "start_time": subtitles[second_half_indices[0]]["start_time"],
                                "end_time": subtitles[second_half_indices[-1]]["end_time"],
                                "text": second_half_text,
                                "title": second_half_title,
                                "original_indices": second_half_indices,
                            }

                            adjusted_subtitles.append(first_half)
                            adjusted_subtitles.append(second_half)
                            continue

                # 如果不需要分割或无法分割，直接添加原段落
                adjusted_subtitles.append(segment)

            # 更新合并后的字幕列表
            if len(adjusted_subtitles) > len(merged_subtitles):
                merged_subtitles = adjusted_subtitles
                logger.info(f"智能分割完成，调整后的段落数量: {len(merged_subtitles)}")
            else:
                logger.warning("无法进行有效的段落分割，保留原始段落")

        # 如果段落数量仍不符合预期，记录日志
        if len(merged_subtitles) < target_min or len(merged_subtitles) > target_max:
            logger.warning(f"最终生成的段落数量({len(merged_subtitles)})不符合目标范围({target_min}-{target_max})")

        logger.info(f"Ollama语义分段完成，共{len(merged_subtitles)}个语义段落")
        return merged_subtitles

    except Exception as e:
        logger.error(f"使用Ollama合并字幕时出错: {str(e)}")
        logger.info("Ollama方法失败，使用方案二")

    # 如果Ollama方法失败，使用方案二
    return merge_subtitles_by_semantics(subtitles)


def merge_subtitles_by_semantics(subtitles, distance_threshold=0.5):
    """基于语义相似度合并字幕并生成标题"""
    logger = logging.getLogger(__name__)

    if not subtitles:
        logger.warning("没有提供字幕数据进行合并")
        return []

    try:
        # 如果字幕数量太少，直接返回
        if len(subtitles) <= 6:
            merged = {
                'title': generate_title_with_llm(' '.join([sub['text'] for sub in subtitles])),
                'start_time': subtitles[0]['start_time'],
                'end_time': subtitles[-1]['end_time'],
                'text': format_text_with_llm(' '.join([sub['text'] for sub in subtitles])),
                'original_subtitles': [
                    {'start_time': sub['start_time'], 'end_time': sub['end_time'], 'text': sub['text']}
                    for sub in subtitles
                ],
            }
            return [merged]

        # 提取字幕文本和时间戳
        texts = [sub['text'] for sub in subtitles]
        logger.info(f"提取了{len(texts)}条字幕文本")

        # 判断是否为长视频（超过150条字幕）
        is_long_video = len(subtitles) > 150

        # 使用LLM API进行语义分段
        try:
            # 创建OpenAI客户端，使用固定的API密钥
            client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

            # 构建所有字幕文本
            full_text = ""
            for i, sub in enumerate(subtitles):
                full_text += f"[{i}] {sub['text']}\n"

            # 构建提示词 - 根据视频长度调整提示词
            if is_long_video:
                # 长视频提示词 - 根据字幕数量确定分段数量
                subtitle_count = len(subtitles)

                # 根据字幕数量确定段落数量和每段字幕数量
                if subtitle_count < 200:
                    segment_count = "8-12个段落"
                    segment_size = "10-20条之间"
                elif subtitle_count < 400:
                    segment_count = "12-18个段落"
                    segment_size = "15-30条之间"
                else:
                    segment_count = "15-25个段落"
                    segment_size = "20-40条之间"

                prompt_template = """请分析以下视频字幕文本，并根据内容的语义连贯性将其分成若干个有意义的段落。

字幕文本（每行前面的数字是字幕的索引）：
{text}

要求：
1. 根据内容的语义连贯性和主题变化进行分段，而不是简单地按固定间隔分段
2. 每个段落应该表达一个相对完整的意思或主题
3. 返回JSON格式的结果，包含每个段落的开始和结束字幕索引
4. 由于这个视频有{subtitle_count}条字幕，请尽量细致地分段，建议生成{segment_count}
5. 每个段落不要太长，建议每个段落包含的字幕数量在{segment_size}
6. 确保分段是连续的，不要有重叠或遗漏

返回格式示例：
```
[
  {"start_index": 0, "end_index": 15, "reason": "介绍了主题背景"},
  {"start_index": 16, "end_index": 32, "reason": "讨论了第一个要点"},
  {"start_index": 33, "end_index": 48, "reason": "总结了结论"}
]
```

请直接返回JSON格式的结果，不要有任何解释或其他内容。"""
            else:
                # 短视频提示词 - 根据字幕数量确定分段
                subtitle_count = len(subtitles)

                # 根据字幕数量确定段落数量 - 与Ollama方案保持一致
                if subtitle_count < 20:  # 字幕很少
                    target_segments = "2-3"
                    segment_guidance = f"{target_segments}个段落"
                elif subtitle_count < 50:  # 字幕较少
                    target_segments = "4-6"
                    segment_guidance = f"{target_segments}个段落"
                elif subtitle_count < 100:  # 字幕中等
                    target_segments = "10-12"
                    segment_guidance = f"{target_segments}个段落"
                elif subtitle_count < 150:  # 字幕较多
                    target_segments = "15-17"
                    segment_guidance = f"{target_segments}个段落"
                elif subtitle_count < 200:  # 字幕很多
                    target_segments = "20-23"
                    segment_guidance = f"{target_segments}个段落"
                elif subtitle_count < 300:  # 字幕非常多
                    target_segments = "23-27"
                    segment_guidance = f"{target_segments}个段落"
                elif subtitle_count < 400:  # 字幕极多
                    target_segments = "29-32"
                    segment_guidance = f"{target_segments}个段落"
                elif subtitle_count < 500:  # 字幕极多
                    target_segments = "34-38"
                    segment_guidance = f"{target_segments}个段落"
                elif subtitle_count < 600:  # 字幕极多
                    target_segments = "40-43"
                    segment_guidance = f"{target_segments}个段落"
                elif subtitle_count < 700:  # 字幕极多
                    target_segments = "44-48"
                    segment_guidance = f"{target_segments}个段落"
                elif subtitle_count < 800:  # 字幕极多
                    target_segments = "49-53"
                    segment_guidance = f"{target_segments}个段落"
                elif subtitle_count < 900:  # 字幕极多
                    target_segments = "54-58"
                    segment_guidance = f"{target_segments}个段落"
                else:  # 字幕数量巨大
                    target_segments = "60-68"
                    segment_guidance = f"{target_segments}个段落"

                # 保存目标段落数量，便于后续处理
                segment_count = int(target_segments.split("-")[1])

                # 从目标段落数量中提取具体数字
                target_min = int(target_segments.split("-")[0])
                target_max = int(target_segments.split("-")[1])
                target_avg = (target_min + target_max) // 2  # 取平均值作为目标

                prompt_template = """请分析以下视频字幕文本，并根据内容的语义连贯性将其分成若干个有意义的段落。

字幕文本（每行前面的数字是字幕的索引）：
{text}

要求：
1. 根据内容的语义连贯性和主题变化进行分段，而不是简单地按固定间隔分段
2. 每个段落应该表达一个相对完整的意思或主题
3. 返回JSON格式的结果，包含每个段落的开始和结束字幕索引
4. 【重要】这个视频共有{subtitle_count}条字幕，你必须严格生成{target_avg}个段落（允许误差±2个）
5. 【重要】请确保生成的段落数量在{target_min}到{target_max}之间，这是硬性要求
6. 确保分段是连续的，不要有重叠或遗漏
7. 段落之间的大小应该相对均衡，避免某些段落过大而其他段落过小

返回格式示例：
```
[
  {"start_index": 0, "end_index": 5, "reason": "介绍了主题背景"},
  {"start_index": 6, "end_index": 12, "reason": "讨论了第一个要点"},
  {"start_index": 13, "end_index": 20, "reason": "总结了结论"}
]
```

请直接返回JSON格式的结果，不要有任何解释或其他内容。"""

            # 使用安全的方式替换变量
            prompt = prompt_template.replace("{text}", full_text)
            prompt = prompt.replace("{subtitle_count}", str(subtitle_count))
            # 只在长视频时才使用segment_count和segment_size
            if is_long_video:
                prompt = prompt.replace("{segment_count}", str(segment_count))
                prompt = prompt.replace("{segment_size}", str(segment_size))
            else:
                # 短视频使用segment_guidance
                prompt = prompt.replace("{segment_guidance}", segment_guidance)

            # 调用API
            response = client.chat.completions.create(
                model="qwen-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的视频内容分析助手。你的任务是分析视频字幕，并根据语义将其分成有意义的段落。"
                        + ("对于长视频，请尽量细致地分段，生成更多的段落。" if is_long_video else ""),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # 使用较低的温度以获得更确定性的结果
            )

            # 获取响应文本
            response_text = response.choices[0].message.content.strip()

            # 从响应文本中提取JSON部分
            json_match = re.search(r'```\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个响应
                json_str = response_text

            # 清理JSON字符串，移除可能的非JSON内容
            json_str = re.sub(r'^[^[{]*', '', json_str)
            json_str = re.sub(r'[^}\]]*$', '', json_str)

            try:
                segments_info = json.loads(json_str)
            except json.JSONDecodeError:
                logger.error(f"无法解析JSON响应: {json_str}")
                raise Exception("无法解析LLM返回的JSON")

            # 确保segments_info是列表类型
            if not isinstance(segments_info, list):
                logger.error(f"解析的JSON不是列表类型: {segments_info}")
                raise Exception("LLM返回的JSON格式不正确")

            # 合并字幕
            merged_subtitles = []
            for segment in segments_info:
                start_index = segment.get("start_index")
                end_index = segment.get("end_index")
                reason = segment.get("reason", "")

                if start_index is None or end_index is None:
                    logger.warning(f"段落信息不完整: {segment}")
                    continue

                # 确保索引在有效范围内
                start_index = max(0, min(start_index, len(subtitles) - 1))
                end_index = max(start_index, min(end_index, len(subtitles) - 1))

                # 合并字幕文本
                segment_text = " ".join([subtitles[i]["text"] for i in range(start_index, end_index + 1)])

                # 使用LLM生成标题
                title = generate_title_with_llm(segment_text)

                # 创建合并后的字幕
                merged_subtitle = {
                    "start_time": subtitles[start_index]["start_time"],
                    "end_time": subtitles[end_index]["end_time"],
                    "text": format_text_with_llm(segment_text),
                    "title": title,
                    "original_indices": list(range(start_index, end_index + 1)),
                }

                merged_subtitles.append(merged_subtitle)

            logger.info(f"LLM语义分段完成，共{len(merged_subtitles)}个语义段落")
            return merged_subtitles

        except Exception as e:
            logger.error(f"使用LLM API进行语义分段时出错: {str(e)}")
            # 确保导入traceback模块
            import traceback as tb

            logger.error(f"错误详情: {tb.format_exc()}")
            # 如果LLM API语义分段失败，回退到基于时间的分段方法
            logger.warning("LLM API语义分段失败，回退到基于时间的分段方法")

        # 如果LLM API语义分段失败，使用基于时间的分段方法
        # 第一轮：强制按时间间隔分段
        # 这一步确保即使字幕内容相似，也会按照时间间隔强制分段
        video_duration = subtitles[-1]['end_time'] - subtitles[0]['start_time']

        # 根据视频长度决定时间间隔
        if video_duration < 300:  # 小于5分钟
            # 每30秒强制分段
            time_segment_interval = 30
        elif video_duration < 1200:  # 5-20分钟
            # 每60秒强制分段
            time_segment_interval = 60
        else:  # 大于20分钟
            # 每120秒强制分段
            time_segment_interval = 120

        # 按照固定时间间隔强制分段
        time_segments = []
        current_segment = []
        segment_start_time = subtitles[0]['start_time']

        for sub in subtitles:
            # 如果当前字幕的开始时间超过了段落的结束时间，开始新段落
            if sub['start_time'] - segment_start_time >= time_segment_interval:
                if current_segment:
                    time_segments.append(current_segment)
                    current_segment = []
                    segment_start_time = sub['start_time']

            current_segment.append(sub)

        # 添加最后一个段落
        if current_segment:
            time_segments.append(current_segment)

        logger.info(f"按时间间隔强制分段完成，共{len(time_segments)}个时间段落")

        # 第二轮：在每个时间段内，基于时间连续性进行初步合并
        merged_segments = []

        for segment in time_segments:
            # 在每个时间段内进行基于时间连续性的合并
            current_group = {
                'start_time': segment[0]['start_time'],
                'end_time': segment[0]['end_time'],
                'text': segment[0]['text'],
                'subtitles': [segment[0]],
            }

            # 设置时间间隔阈值（秒）
            time_threshold = 2.0

            for i in range(1, len(segment)):
                current_sub = segment[i]
                prev_sub = segment[i - 1]

                # 检查时间连续性
                time_diff = current_sub['start_time'] - prev_sub['end_time']
                time_continuous = time_diff < time_threshold

                # 如果时间连续，继续合并
                if time_continuous:
                    current_group['end_time'] = current_sub['end_time']
                    current_group['text'] += ' ' + current_sub['text']
                    current_group['subtitles'].append(current_sub)
                else:
                    # 否则，结束当前组并开始新组
                    if len(current_group['text']) > 0:
                        merged_segments.append(current_group)

                    # 创建新组
                    current_group = {
                        'start_time': current_sub['start_time'],
                        'end_time': current_sub['end_time'],
                        'text': current_sub['text'],
                        'subtitles': [current_sub],
                    }

            # 添加最后一组
            if len(current_group['text']) > 0:
                merged_segments.append(current_group)

        logger.info(f"时间连续性合并完成，共{len(merged_segments)}个合并后的段落")

        # 直接使用第二轮合并的结果
        final_merged = merged_segments

        # 格式化最终结果
        result = []
        for group in final_merged:
            # 生成标题
            title = generate_title(group['text'])

            # 添加到结果列表
            result.append(
                {
                    'title': title,
                    'start_time': group['start_time'],
                    'end_time': group['end_time'],
                    'text': format_text_with_llm(group['text']),
                    'original_subtitles': [
                        {'start_time': sub['start_time'], 'end_time': sub['end_time'], 'text': sub['text']}
                        for sub in group['subtitles']
                    ],
                }
            )

        logger.info(f"最终合并完成，共{len(result)}条合并后的字幕")

        return result
    except Exception as e:
        logger.error(f"合并字幕时出错: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return []


def format_text_with_ollama(text):
    """使用Ollama为文本添加适当的标点符号，并使用重试机制"""
    logger = logging.getLogger(__name__)

    # 如果文本为空，直接返回
    if not text or text.strip() == "":
        return text

    try:
        # 构建提示词
        prompt_template = """请为以下文本添加适当的标点符号，使其更易于阅读。保持原文意思不变，只添加标点符号：

{text}

要求：
1. 只添加标点符号，不要改变原文内容
2. 不要添加额外的解释或评论
3. 直接返回添加了标点符号的文本，不要有任何其他内容
4. 如果原文已有标点，保留原有标点"""

        # 替换变量
        prompt = prompt_template.replace("{text}", text)

        # 创建带重试机制的会话
        session = create_retry_session()

        # 定义重试函数
        def call_ollama_with_retry(max_retries=OLLAMA_MAX_RETRIES):
            retries = 0
            while retries <= max_retries:
                try:
                    # 在重试前添加随机延迟
                    if retries > 0:
                        wait_time = OLLAMA_RETRY_BACKOFF**retries
                        logger.info(f"格式化文本第{retries}次重试，等待{wait_time:.2f}秒")
                        time.sleep(wait_time)

                    # 调用Ollama API
                    response = session.post(
                        OLLAMA_BASE_URL + "/generate",
                        json={
                            "model": OLLAMA_MODEL,
                            "prompt": prompt,
                            "stream": False,
                            "options": {"temperature": 0.3},
                        },
                        timeout=OLLAMA_REQUEST_TIMEOUT,  # 使用配置的超时时间
                    )

                    if response.status_code != 200:
                        logger.error(f"Ollama API调用失败: {response.status_code} {response.text}")
                        retries += 1
                        continue

                    # 获取响应文本
                    formatted_text = response.json().get("response", "").strip()

                    # 如果返回为空，重试
                    if not formatted_text:
                        logger.warning("Ollama返回的格式化文本为空，尝试重试")
                        retries += 1
                        continue

                    logger.info("成功使用Ollama添加标点符号")
                    return formatted_text

                except Exception as e:
                    logger.error(f"使用Ollama添加标点符号时出错: {str(e)}")
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"超过最大重试次数，将使用原始文本")
                        return None

            return None

        # 调用重试函数
        result = call_ollama_with_retry()
        if result:
            return result
        else:
            # 如果Ollama失败，尝试使用备用方法
            logger.info("尝试使用备用方法格式化文本")
            try:
                return format_text_with_llm(text)
            except Exception as e:
                logger.error(f"备用格式化方法也失败: {str(e)}")
                return text
    except Exception as e:
        logger.error(f"格式化文本时出错: {str(e)}")
        return text


def format_text_with_llm(text):
    """使用LLM API为文本添加适当的标点符号"""
    logger = logging.getLogger(__name__)

    if not text or len(text) < 5:
        return text

    try:
        # 创建OpenAI客户端，使用固定的API密钥
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

        # 构建提示词
        prompt_template = """请为以下文本添加适当的标点符号，使其更易于阅读和理解：

文本内容：
{text}

要求：
1. 保持原文的意思不变
2. 添加合适的标点符号（如句号、逗号、问号、感叹号等）
3. 修正明显的语法错误
4. 直接返回处理后的文本，不要有任何解释或其他内容"""

        # 使用安全的方式替换变量
        prompt = prompt_template.replace("{text}", text)

        # 调用API
        response = client.chat.completions.create(
            model="qwen-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的文本编辑助手。你的任务是为文本添加适当的标点符号，使其更易于阅读和理解。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # 使用较低的温度以获得更确定性的结果
        )

        # 获取生成的文本
        formatted_text = response.choices[0].message.content.strip()

        # 如果返回为空，使用原始文本
        if not formatted_text:
            logger.warning("LLM API返回的格式化文本为空，使用原始文本")
            return text

        logger.info("成功使用LLM API添加标点符号")
        return formatted_text

    except Exception as e:
        logger.error(f"使用LLM API添加标点符号时出错: {str(e)}")
        # 出错时使用原始文本
        return text


def generate_title_with_llm(text):
    """使用LLM API生成标题"""
    logger = logging.getLogger(__name__)

    if not text or len(text) < 5:
        return text

    try:
        # 创建OpenAI客户端，使用固定的API密钥
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

        # 构建提示词
        prompt_template = """请为以下文本生成一个简短的标题（不超过8个字符）：

文本内容：
{text}

要求：
1. 标题应该简洁明了，不超过8个字符
2. 标题应该能够准确反映文本的核心内容和主题
3. 不要使用"关于..."、"论..."等形式
4. 直接返回标题，不要有任何解释或其他内容"""

        # 使用安全的方式替换变量
        prompt = prompt_template.replace("{text}", text)

        # 调用API
        response = client.chat.completions.create(
            model="qwen-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的标题生成助手。你的任务是为给定的文本生成简短、准确的标题。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # 使用较低的温度以获得更确定性的结果
        )

        # 获取生成的标题
        title = response.choices[0].message.content.strip()

        # 记录生成的标题长度
        if len(title) > 8:
            logger.warning(f"生成的标题长度超过8个字符: {title}")

        logger.info(f"LLM生成的标题: {title}")
        return title

    except Exception as e:
        logger.error(f"使用LLM生成标题时出错: {str(e)}")
        # 出错时回退到传统方法
        return generate_title_traditional(text)


def generate_title_traditional(text, max_words=4):
    """使用传统NLP方法生成标题（作为备选方案）"""
    logger = logging.getLogger(__name__)

    try:
        # 如果文本太短，直接返回
        if len(text) < 10:
            return text

        # 使用jieba的TextRank提取关键词
        keywords = jieba.analyse.textrank(text, topK=max_words)

        # 如果没有提取到关键词，返回文本的前几个字作为标题
        if not keywords:
            return text[:10] + '...' if len(text) > 10 else text

        # 将关键词组合成标题
        title = ''.join(keywords)
        if len(title) > 10:
            title = title[:10]

        return title
    except Exception as e:
        logger.error(f"生成标题时出错: {str(e)}")
        # 出错时返回一个简单的标题
        return text[:10] + '...' if len(text) > 10 else text


def generate_title_with_ollama(text):
    """使用Ollama模型生成标题，并使用重试机制"""
    logger = logging.getLogger(__name__)

    # 如果文本为空，返回默认标题
    if not text or text.strip() == "":
        return "无标题"

    try:
        # 如果文本过长，截取前面的部分
        if len(text) > 1000:
            text = text[:1000] + "..."

        # 构建提示词
        prompt_template = """请为以下文本生成一个简短的标题（不超过10个字），标题应准确反映文本的主要内容和主题：

{text}

要求：
1. 标题应简洁明确，不超过10个字
2. 标题应能准确反映文本的主要内容和主题
3. 不要使用太简单或太空泛的标题
4. 直接返回标题，不要有任何其他内容
5. 不要使用引号或其他特殊格式"""

        # 替换变量
        prompt = prompt_template.replace("{text}", text)

        # 创建带重试机制的会话
        session = create_retry_session()

        # 定义重试函数
        def call_ollama_with_retry(max_retries=OLLAMA_MAX_RETRIES):
            retries = 0
            while retries <= max_retries:
                try:
                    # 在重试前添加随机延迟
                    if retries > 0:
                        wait_time = OLLAMA_RETRY_BACKOFF**retries
                        logger.info(f"生成标题第{retries}次重试，等待{wait_time:.2f}秒")
                        time.sleep(wait_time)

                    # 调用Ollama API
                    response = session.post(
                        OLLAMA_BASE_URL + "/generate",
                        json={
                            "model": OLLAMA_MODEL,
                            "prompt": prompt,
                            "stream": False,
                            "options": {"temperature": 0.3},
                        },
                        timeout=OLLAMA_REQUEST_TIMEOUT,  # 使用配置的超时时间
                    )

                    if response.status_code != 200:
                        logger.error(f"Ollama API调用失败: {response.status_code} {response.text}")
                        retries += 1
                        continue

                    # 获取响应文本
                    title = response.json().get("response", "").strip()

                    # 如果返回为空，重试
                    if not title:
                        logger.warning("Ollama返回的标题为空，尝试重试")
                        retries += 1
                        continue

                    # 限制标题长度
                    if len(title) > 20:  # 给一些缓冲空间
                        title = title[:20]

                    logger.info(f"成功使用Ollama生成标题: {title}")
                    return title

                except Exception as e:
                    logger.error(f"使用Ollama生成标题时出错: {str(e)}")
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"超过最大重试次数，将使用备用方法")
                        return None

            return None

        # 调用重试函数
        result = call_ollama_with_retry()
        if result:
            return result
        else:
            # 如果Ollama失败，尝试使用备用方法
            logger.info("尝试使用备用方法生成标题")
            try:
                return generate_title_with_llm(text)
            except Exception as e:
                logger.error(f"备用标题生成方法也失败: {str(e)}")
                return generate_title_traditional(text)
    except Exception as e:
        logger.error(f"生成标题时出错: {str(e)}")
        return generate_title_traditional(text)


def generate_title(text):
    """生成标题的主函数，优先使用Ollama，失败时回退到其他方法"""
    try:
        # 优先使用Ollama生成标题
        return generate_title_with_ollama(text)
    except Exception as e:
        logger.error(f"使用Ollama生成标题失败，回退到LLM: {str(e)}")
        # 如果失败，尝试使用LLM
        try:
            return generate_title_with_llm(text)
        except Exception as e2:
            logger.error(f"使用LLM生成标题也失败，回退到传统方法: {str(e2)}")
            # 如果再次失败，使用传统方法
            return generate_title_traditional(text)
        logger.warning("没有提供字幕数据进行合并")
        return []

    try:
        # 如果字幕数量太少，直接返回
        if len(subtitles) <= 6:
            merged = {
                'title': generate_title(' '.join([sub['text'] for sub in subtitles])),
                'start_time': subtitles[0]['start_time'],
                'end_time': subtitles[-1]['end_time'],
                'text': format_text_with_llm(' '.join([sub['text'] for sub in subtitles])),
                'original_subtitles': [
                    {'start_time': sub['start_time'], 'end_time': sub['end_time'], 'text': sub['text']}
                    for sub in subtitles
                ],
            }
            return [merged]

        # 提取字幕文本和时间戳
        texts = [sub['text'] for sub in subtitles]
        logger.info(f"提取了{len(texts)}条字幕文本")

        # 第一轮：强制按时间间隔分段
        # 这一步确保即使字幕内容相似，也会按照时间间隔强制分段
        video_duration = subtitles[-1]['end_time'] - subtitles[0]['start_time']

        # 根据视频长度决定时间间隔
        if video_duration < 300:  # 小于5分钟
            # 每30秒强制分段
            time_segment_interval = 30
        elif video_duration < 1200:  # 5-20分钟
            # 每60秒强制分段
            time_segment_interval = 60
        else:  # 大于20分钟
            # 每120秒强制分段
            time_segment_interval = 120

        # 按照固定时间间隔强制分段
        time_segments = []
        current_segment = []
        segment_start_time = subtitles[0]['start_time']

        for sub in subtitles:
            # 如果当前字幕的开始时间超过了段落的结束时间，开始新段落
            if sub['start_time'] - segment_start_time >= time_segment_interval:
                if current_segment:
                    time_segments.append(current_segment)
                    current_segment = []
                    segment_start_time = sub['start_time']

            current_segment.append(sub)

        # 添加最后一个段落
        if current_segment:
            time_segments.append(current_segment)

        logger.info(f"按时间间隔强制分段完成，共{len(time_segments)}个时间段落")

        # 第二轮：在每个时间段内，基于时间连续性进行初步合并
        merged_segments = []

        for segment in time_segments:
            # 在每个时间段内进行基于时间连续性的合并
            current_group = {
                'start_time': segment[0]['start_time'],
                'end_time': segment[0]['end_time'],
                'text': segment[0]['text'],
                'subtitles': [segment[0]],
            }

            # 设置时间间隔阈值（秒）
            time_threshold = 2.0

            for i in range(1, len(segment)):
                current_sub = segment[i]
                prev_sub = segment[i - 1]

                # 检查时间连续性
                time_diff = current_sub['start_time'] - prev_sub['end_time']
                time_continuous = time_diff < time_threshold

                # 如果时间连续，继续合并
                if time_continuous:
                    current_group['end_time'] = current_sub['end_time']
                    current_group['text'] += ' ' + current_sub['text']
                    current_group['subtitles'].append(current_sub)
                else:
                    # 否则，结束当前组并开始新组
                    if len(current_group['text']) > 0:
                        merged_segments.append(current_group)

                    # 创建新组
                    current_group = {
                        'start_time': current_sub['start_time'],
                        'end_time': current_sub['end_time'],
                        'text': current_sub['text'],
                        'subtitles': [current_sub],
                    }

            # 添加最后一组
            if len(current_group['text']) > 0:
                merged_segments.append(current_group)

        logger.info(f"时间连续性合并完成，共{len(merged_segments)}个合并后的段落")

        # 直接使用第二轮合并的结果
        final_merged = merged_segments

        # 格式化最终结果
        result = []
        for group in final_merged:
            # 生成标题
            title = generate_title(group['text'])

            # 添加到结果列表
            result.append(
                {
                    'title': title,
                    'start_time': group['start_time'],
                    'end_time': group['end_time'],
                    'text': format_text_with_llm(group['text']),
                    'original_subtitles': [
                        {'start_time': sub['start_time'], 'end_time': sub['end_time'], 'text': sub['text']}
                        for sub in group['subtitles']
                    ],
                }
            )

        logger.info(f"最终合并完成，共{len(result)}条合并后的字幕")

        return result
    except Exception as e:
        logger.error(f"合并字幕时出错: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return []


def _fix_json_format(json_str):
    """修复常见的JSON格式错误，如缺少逗号、引号等"""
    logger = logging.getLogger(__name__)

    # 记录原始JSON字符串用于调试
    logger.debug(f"尝试修复JSON格式: {json_str[:100]}...")

    # 移除行号前缀，如 "15: "end_index": 27" 中的 "15: "
    json_str = re.sub(r'\s*\d+\s*:\s*"', '"', json_str)

    # 修复缺少逗号的问题
    json_str = re.sub(r'}\s*{', '},{', json_str)
    json_str = re.sub(r'"\s*{', '",{', json_str)
    json_str = re.sub(r'}\s*"', '},"', json_str)

    # 修复缺少逗号的问题 - 特别是在JSON对象内部
    # 查找形如 "key": "value" "key": "value" 的模式（缺少逗号）
    json_str = re.sub(r'"\s*}\s*"', '"},"', json_str)

    # 修复特定的格式问题 - 在属性之间添加缺失的逗号
    pattern = r'("formatted_text"\s*:\s*"[^"]*")\s*("title"\s*:)'
    json_str = re.sub(pattern, r'\1,\2', json_str)

    # 修复错误的属性名格式 - 例如 "start_index": 13, 14: 25 应改为 "start_index": 13, "end_index": 25
    json_str = re.sub(r'(\d+)\s*:\s*(\d+)', r'"end_index": \2', json_str)

    # 修复缺少引号的属性名
    json_str = re.sub(r'([{,])\s*(\w+)\s*:', r'\1"\2":', json_str)

    # 修复缺少逗号的属性
    json_str = re.sub(r'("\w+"\s*:\s*[^{\[,\s][^{\[,]*?)\s*("\w+"\s*:)', r'\1,\2', json_str)

    # 移除可能存在的行号和冒号格式 (如 "12: " 或 "end_index": 27, 28: "formatted_text")
    json_str = re.sub(r',\s*\d+\s*:\s*"', ',"', json_str)

    # 确保JSON数组正确关闭
    if not json_str.strip().endswith(']'):
        json_str = json_str.rstrip() + ']'

    # 确保JSON数组正确开始
    if not json_str.strip().startswith('['):
        json_str = '[' + json_str.lstrip()

    # 记录修复后的JSON字符串
    logger.debug(f"修复后的JSON格式: {json_str[:100]}...")

    return json_str
