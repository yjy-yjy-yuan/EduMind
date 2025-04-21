import jieba
import jieba.analyse
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
import logging
import re
import os
import json
import requests
import traceback
from openai import OpenAI

# 直接使用固定的API密钥（与chat_system.py保持一致）
OPENAI_API_KEY = "sk-178e130a121445659860893fdfae1e7d"
OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# Ollama API配置
OLLAMA_BASE_URL = "http://localhost:11434/api"
OLLAMA_MODEL = "qwen2.5:7b"  # 默认使用qwen2.5:7b模型，可以根据需要更改

def check_ollama_service():
    """检查Ollama服务是否可用"""
    logger = logging.getLogger(__name__)
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/tags", timeout=5)
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
    """分块处理长视频字幕"""
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
    
    # 使用线程池并行处理字幕块
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # 准备任务列表
        future_to_chunk = {}
        
        # 提交所有任务到线程池
        for i in range(0, len(subtitles), chunk_size):
            end_idx = min(i + chunk_size, len(subtitles))
            chunk = subtitles[i:end_idx]
            
            logger.info(f"提交字幕块 {i}-{end_idx-1} 到线程池，共{len(chunk)}条字幕")
            future = executor.submit(process_subtitle_chunk, chunk, i)
            future_to_chunk[future] = (i, end_idx-1)
        
        # 收集结果
        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk_range = future_to_chunk[future]
            try:
                chunk_results = future.result()
                if chunk_results:
                    all_results.extend(chunk_results)
                    logger.info(f"字幕块 {chunk_range[0]}-{chunk_range[1]} 处理完成，生成了 {len(chunk_results)} 个段落")
            except Exception as e:
                logger.error(f"处理字幕块 {chunk_range[0]}-{chunk_range[1]} 时出错: {str(e)}")
                # 记录错误但继续处理其他块
                logger.error(traceback.format_exc())
    
    # 按照开始时间排序结果
    all_results.sort(key=lambda x: x["start_time"])
    
    logger.info(f"长视频分块处理完成，共生成{len(all_results)}个语义段落")
    return all_results

def process_subtitle_chunk(chunk, start_offset):
    """处理单个字幕块"""
    logger = logging.getLogger(__name__)
    # 提取字幕文本
    chunk_text = ""
    for i, subtitle in enumerate(chunk):
        chunk_text += f"{i+1}. {subtitle['text']}\n"
    
    # 构建提示词 - 简化提示词以加快处理速度
    prompt_template = """请分析以下字幕文本，按语义将其分成若干段落，并为每个段落生成标题。

{{ text }}

要求：
1. 基于语义内容进行分段，相关主题应该在同一段落中
2. 为每个段落添加适当的标点符号，使其更易于阅读
3. 确保每个段落的开始和结束索引正确
4. 为每个段落生成一个简短的标题（不超过10个字）

返回格式（JSON）：
```
[
  {{
    "start_index": 0,
    "end_index": 5,
    "formatted_text": "这是添加了标点符号的文本。这样更容易阅读和理解。",
    "title": "主题介绍"
  }},
  {{
    "start_index": 6,
    "end_index": 12,
    "formatted_text": "这是第二段添加了标点符号的文本。",
    "title": "要点讨论"
  }}
]
```

请直接返回JSON格式的结果，不要有任何解释或其他内容。"""
    # 替换变量
    prompt = prompt_template.replace("{{ text }}", chunk_text)
    
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
                        "num_predict": 1024  # 限制生成的token数量
                    }
                },
                timeout=30  # 减少超时时间
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
            
            # 如果没有格式化文本，使用原始合并文本
            if not formatted_text:
                formatted_text = " ".join([chunk[i]["text"] for i in range(chunk_start_index, chunk_end_index + 1)])
            
            title = segment.get("title", f"段落{len(results)+1}")
            
            # 获取时间信息
            start_time = chunk[chunk_start_index]["start_time"]
            end_time = chunk[chunk_end_index]["end_time"]
            
            results.append({
                "start_time": start_time,
                "end_time": end_time,
                "text": formatted_text,
                "title": title,
                "original_indices": list(range(global_start_index, global_end_index + 1))
            })
        
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
            segment_guidance = "应该生成4-5个段落，确保每个段落内容连贯"
        elif subtitle_count < 100:  # 字幕中等
            segment_guidance = "应该生成8-9个段落，合理划分主题"
        elif subtitle_count < 150:  # 字幕较多
            segment_guidance = "应该生成11-12个段落，确保主题清晰划分"
        elif subtitle_count < 200:  # 字幕很多
            segment_guidance = "应该生成14-15个段落，确保主题清晰划分"
        elif subtitle_count < 300:  # 字幕非常多
            segment_guidance = "应该生成17-18个段落，确保主题清晰划分"
        elif subtitle_count < 400:  # 字幕极多
            segment_guidance = "应该生成19-20个段落，确保主题清晰划分"
        else:  # 字幕数量巨大
            segment_guidance = "应该生成20-22个段落，确保主题清晰划分"
            
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
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3
                    }
                },
                timeout=60
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
        if subtitle_count < 20:  # 字幕很少
            target_segments_count = 3  # 目标为2-3个段落
        elif subtitle_count < 50:  # 字幕较少
            target_segments_count = 5  # 目标为4-5个段落
        elif subtitle_count < 100:  # 字幕中等
            target_segments_count = 8  # 目标为8-9个段落
        elif subtitle_count < 150:  # 字幕较多
            target_segments_count = 10  # 目标为11-12个段落
        elif subtitle_count < 200:  # 字幕很多
            target_segments_count = 15  # 目标为14-15个段落
        elif subtitle_count < 300:  # 字幕非常多
            target_segments_count = 18  # 目标为17-19个段落
        elif subtitle_count < 400:  # 字幕极多
            target_segments_count = 22  # 目标为21-23个段落
        elif subtitle_count < 500:  # 字幕极多
            target_segments_count = 25  # 目标为24-26个段落
        elif subtitle_count < 600:  # 字幕极多
            target_segments_count = 28  # 目标为27-29个段落
        elif subtitle_count < 700:  # 字幕极多
            target_segments_count = 31  # 目标为30-32个段落
        elif subtitle_count < 800:  # 字幕极多
            target_segments_count = 35  # 目标为34-36个段落
        elif subtitle_count < 900:  # 字幕极多
            target_segments_count = 38  # 目标为37-39个段落
        else:  # 字幕数量巨大
            target_segments_count = 42  # 目标为40-43个段落
        
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
            
            # 如果没有标题，生成一个简单的标题
            if not title:
                title = f"第{len(merged_subtitles) + 1}部分"
            
            # 创建合并后的字幕，使用原始文本
            merged_subtitle = {
                "start_time": subtitles[start_index]["start_time"],
                "end_time": subtitles[end_index]["end_time"],
                "text": original_text,
                "title": title,
                "original_indices": list(range(start_index, end_index + 1))
            }
            
            merged_subtitles.append(merged_subtitle)
        
        # 检查段落数量是否符合要求
        actual_segments_count = len(merged_subtitles)
        logger.info(f"模型生成的段落数量: {actual_segments_count}, 目标段落数量: {target_segments_count}")
        
        # 如果没有段落，使用方案二
        if not merged_subtitles:
            logger.warning("Ollama没有返回有效的段落，使用方案二")
            return merge_subtitles_by_semantics(subtitles)
        
        # 如果段落数量远小于目标数量，强制分段
        if actual_segments_count < target_segments_count * 0.7:  # 如果实际段落数量小于目标的70%
            logger.warning(f"段落数量({actual_segments_count})远小于目标数量({target_segments_count})，强制分段")
            
            # 强制分段策略：将现有段落分割成更多段落
            new_merged_subtitles = []
            for segment in merged_subtitles:
                original_indices = segment["original_indices"]
                segment_size = len(original_indices)
                
                # 计算每个段落应该分成几个子段落
                sub_segments_count = max(2, round(segment_size / (subtitle_count / target_segments_count)))
                
                if sub_segments_count <= 1 or segment_size < 6:  # 如果段落太小，不再分割
                    new_merged_subtitles.append(segment)
                    continue
                
                # 将当前段落分成多个子段落
                sub_segment_size = segment_size // sub_segments_count
                for i in range(sub_segments_count):
                    start_pos = i * sub_segment_size
                    end_pos = (i + 1) * sub_segment_size if i < sub_segments_count - 1 else segment_size
                    
                    if start_pos >= end_pos:
                        continue
                    
                    sub_indices = original_indices[start_pos:end_pos]
                    if not sub_indices:
                        continue
                    
                    # 创建新的子段落
                    sub_segment = {
                        "start_time": subtitles[sub_indices[0]]["start_time"],
                        "end_time": subtitles[sub_indices[-1]]["end_time"],
                        "text": " ".join([subtitles[i]["text"] for i in sub_indices]),
                        "title": f"{segment['title']}-第{i+1}部分",
                        "original_indices": sub_indices
                    }
                    
                    new_merged_subtitles.append(sub_segment)
            
            merged_subtitles = new_merged_subtitles
            logger.info(f"强制分段后的段落数量: {len(merged_subtitles)}")
        
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
                'original_subtitles': [{'start_time': sub['start_time'], 
                                      'end_time': sub['end_time'], 
                                      'text': sub['text']} for sub in subtitles]
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
            client = OpenAI(
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_BASE_URL
            )
            
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
                
                # 根据字幕数量确定段落数量
                if subtitle_count < 30:
                    segment_guidance = "2-3个段落"
                elif subtitle_count < 80:
                    segment_guidance = "3-5个段落"
                else:
                    segment_guidance = "5-8个段落"
                
                prompt_template = """请分析以下视频字幕文本，并根据内容的语义连贯性将其分成若干个有意义的段落。
                
字幕文本（每行前面的数字是字幕的索引）：
{text}

要求：
1. 根据内容的语义连贯性和主题变化进行分段，而不是简单地按固定间隔分段
2. 每个段落应该表达一个相对完整的意思或主题
3. 返回JSON格式的结果，包含每个段落的开始和结束字幕索引
4. 根据字幕总数（共{subtitle_count}条），应该生成{segment_guidance}，确保每个段落内容连贯
5. 确保分段是连续的，不要有重叠或遗漏

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
            prompt = prompt.replace("{segment_count}", segment_count)
            prompt = prompt.replace("{segment_size}", segment_size) if is_long_video else prompt.replace("{segment_guidance}", segment_guidance)
            
            # 调用API
            response = client.chat.completions.create(
                model="qwen-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的视频内容分析助手。你的任务是分析视频字幕，并根据语义将其分成有意义的段落。" + 
                     ("对于长视频，请尽量细致地分段，生成更多的段落。" if is_long_video else "")},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3  # 使用较低的温度以获得更确定性的结果
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
                    "original_indices": list(range(start_index, end_index + 1))
                }
                
                merged_subtitles.append(merged_subtitle)
            
            logger.info(f"LLM语义分段完成，共{len(merged_subtitles)}个语义段落")
            return merged_subtitles
            
        except Exception as e:
            logger.error(f"使用LLM API进行语义分段时出错: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
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
                'subtitles': [segment[0]]
            }
            
            # 设置时间间隔阈值（秒）
            time_threshold = 2.0
            
            for i in range(1, len(segment)):
                current_sub = segment[i]
                prev_sub = segment[i-1]
                
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
                        'subtitles': [current_sub]
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
            result.append({
                'title': title,
                'start_time': group['start_time'],
                'end_time': group['end_time'],
                'text': format_text_with_llm(group['text']),
                'original_subtitles': [{'start_time': sub['start_time'], 
                                      'end_time': sub['end_time'], 
                                      'text': sub['text']} for sub in group['subtitles']]
            })
        
        logger.info(f"最终合并完成，共{len(result)}条合并后的字幕")
        
        return result
    except Exception as e:
        logger.error(f"合并字幕时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def format_text_with_ollama(text):
    """使用Ollama为文本添加适当的标点符号"""
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
        
        # 调用Ollama API
        try:
            response = requests.post(
                OLLAMA_BASE_URL + "/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3
                    }
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API调用失败: {response.status_code} {response.text}")
                raise Exception(f"Ollama API调用失败: {response.status_code}")
            
            # 获取响应文本
            formatted_text = response.json().get("response", "").strip()
            
            # 如果返回为空，使用原始文本
            if not formatted_text:
                logger.warning("Ollama返回的格式化文本为空，使用原始文本")
                return text
            
            logger.info("成功使用Ollama添加标点符号")
            return formatted_text
            
        except Exception as e:
            logger.error(f"使用Ollama添加标点符号时出错: {str(e)}")
            # 出错时使用原始文本
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
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        
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
                {"role": "system", "content": "你是一个专业的文本编辑助手。你的任务是为文本添加适当的标点符号，使其更易于阅读和理解。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # 使用较低的温度以获得更确定性的结果
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
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        
        # 构建提示词
        prompt_template = """请为以下文本生成一个简短的标题（不超过10个字）：

文本内容：
{text}

要求：
1. 标题应该简洁明了，不超过10个字
2. 标题应该能够准确反映文本的核心内容和主题
3. 不要使用"关于..."、"论..."等形式
4. 直接返回标题，不要有任何解释或其他内容"""
        
        # 使用安全的方式替换变量
        prompt = prompt_template.replace("{text}", text)
        
        # 调用API
        response = client.chat.completions.create(
            model="qwen-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的标题生成助手。你的任务是为给定的文本生成简短、准确的标题。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # 使用较低的温度以获得更确定性的结果
        )
        
        # 获取生成的标题
        title = response.choices[0].message.content.strip()
        
        # 如果标题太长，截断它
        if len(title) > 10:
            title = title[:10]
        
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
    """使用Ollama模型生成标题"""
    logger = logging.getLogger(__name__)
    
    if not text or len(text) < 5:
        return text
    
    try:
        # 首先检查Ollama服务是否可用
        if not check_ollama_service():
            logger.warning("Ollama服务不可用，回退到传统标题生成方法")
            return generate_title_traditional(text)
        
        # 构建提示词
        prompt_template = """请为以下文本生成一个简短的标题（不超过10个字）：

文本内容：
{text}

要求：
1. 标题应该简洁明了，不超过10个字
2. 标题应该能够准确反映文本的核心内容和主题
3. 不要使用"关于..."、"论..."等形式
4. 直接返回标题，不要有任何解释或其他内容"""
        
        # 使用安全的方式替换变量
        prompt = prompt_template.replace("{text}", text)
        
        # 调用Ollama API
        response = requests.post(
            OLLAMA_BASE_URL + "/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3
                }
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Ollama API调用失败: {response.status_code} {response.text}")
            # 失败时回退到传统方法
            return generate_title_traditional(text)
        
        # 获取生成的标题
        title = response.json().get("response", "").strip()
        
        # 清理标题，移除可能的引号和多余空格
        title = re.sub(r'^["\'\s]+|["\'\s]+$', '', title)
        
        # 如果标题太长，截断它
        if len(title) > 10:
            title = title[:10]
        
        logger.info(f"Ollama生成的标题: {title}")
        return title
        
    except Exception as e:
        logger.error(f"使用Ollama生成标题时出错: {str(e)}")
        # 出错时回退到传统方法
        return generate_title_traditional(text)

def generate_title(text, max_words=4):
    """生成标题的主函数，优先使用LLM，失败时回退到传统方法"""
    # 优先使用LLM生成标题
    return generate_title_with_llm(text)

def merge_subtitles_by_time_intervals(subtitles):
    """按时间间隔强制分段"""
    logger = logging.getLogger(__name__)
    
    if not subtitles:
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
                'original_subtitles': [{'start_time': sub['start_time'], 
                                      'end_time': sub['end_time'], 
                                      'text': sub['text']} for sub in subtitles]
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
                'subtitles': [segment[0]]
            }
            
            # 设置时间间隔阈值（秒）
            time_threshold = 2.0
            
            for i in range(1, len(segment)):
                current_sub = segment[i]
                prev_sub = segment[i-1]
                
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
                        'subtitles': [current_sub]
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
            result.append({
                'title': title,
                'start_time': group['start_time'],
                'end_time': group['end_time'],
                'text': format_text_with_llm(group['text']),
                'original_subtitles': [{'start_time': sub['start_time'], 
                                      'end_time': sub['end_time'], 
                                      'text': sub['text']} for sub in group['subtitles']]
            })
        
        logger.info(f"最终合并完成，共{len(result)}条合并后的字幕")
        
        return result
    except Exception as e:
        logger.error(f"合并字幕时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def _fix_json_format(json_str):
    """修复常见的JSON格式错误，如缺少逗号、引号等"""
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
    
    # 确保JSON数组正确关闭
    if not json_str.strip().endswith(']'):
        json_str = json_str.rstrip() + ']'
    
    # 确保JSON数组正确开始
    if not json_str.strip().startswith('['):
        json_str = '[' + json_str.lstrip()
    
    return json_str