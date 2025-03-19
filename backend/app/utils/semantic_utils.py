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
    
    # 分块大小
    chunk_size = 100
    
    # 存储所有处理结果
    all_results = []
    
    # 分块处理
    for i in range(0, len(subtitles), chunk_size):
        end_idx = min(i + chunk_size, len(subtitles))
        chunk = subtitles[i:end_idx]
        
        logger.info(f"处理字幕块 {i}-{end_idx-1}，共{len(chunk)}条字幕")
        
        # 处理当前块
        try:
            chunk_results = process_subtitle_chunk(chunk, i)
            if chunk_results:
                all_results.extend(chunk_results)
        except Exception as e:
            logger.error(f"处理字幕块 {i}-{end_idx-1} 时出错: {str(e)}")
            # 如果处理失败，直接抛出异常，让上层函数处理
            raise
    
    logger.info(f"长视频分块处理完成，共生成{len(all_results)}个语义段落")
    return all_results

def process_subtitle_chunk(chunk, start_offset):
    """处理单个字幕块"""
    logger = logging.getLogger(__name__)
    # 提取字幕文本
    chunk_text = ""
    for i, subtitle in enumerate(chunk):
        chunk_text += f"{i+1}. {subtitle['text']}\n"
    
    # 构建提示词
    prompt_template = """请分析以下字幕文本，按语义将其分成若干段落，并为每个段落生成标题。

{{ text }}

要求：
1. 基于语义内容进行分段，相关主题应该在同一段落中
2. 不要生成摘要，保留原始内容
3. 为每个段落添加适当的标点符号，使其更易于阅读
4. 确保每个段落的开始和结束索引正确
5. 提供分段的理由
6. 为每个段落生成一个简短、具体的标题，反映其主要内容

返回格式（JSON）：
```
[
  {{
    "start_index": 0,
    "end_index": 5,
    "reason": "介绍了主题背景",
    "formatted_text": "这是添加了标点符号的文本。这样更容易阅读和理解。",
    "title": "主题介绍"
  }},
  {{
    "start_index": 6,
    "end_index": 12,
    "reason": "讨论了第一个要点",
    "formatted_text": "这是第二段添加了标点符号的文本。包含了完整的标点和语法修正。",
    "title": "要点讨论"
  }}
]
```

请直接返回JSON格式的结果，不要有任何解释或其他内容。确保JSON格式正确，每个属性之间都有逗号分隔。"""
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
                    "stream": False
                },
                timeout=60
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
        prompt_template = """请分析以下视频字幕文本，并完成三个任务：
1. 根据内容的语义连贯性将其分成若干个有意义的段落
2. 为每个段落添加适当的标点符号，使其更易于阅读（注意：返回的文本中不要包含索引标记[0]、[1]等）
3. 为每个段落生成一个简短的标题（不超过15个字）

字幕文本（每行前面的数字是字幕的索引）：
{{ text }}

要求：
1. 根据内容的语义连贯性和主题变化进行分段，而不是简单地按固定间隔分段
2. 每个段落应该表达一个相对完整的意思或主题
3. 对于短视频（不到5分钟），应该生成2-5个段落，不要过度分段
4. 确保分段是连续的，不要有重叠或遗漏
5. 为每个段落添加适当的标点符号，保持原文意思不变
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
        
        # 合并字幕 - 直接使用Ollama返回的格式化文本和标题
        merged_subtitles = []
        try:
            for segment in segments_info:
                start_index = segment.get("start_index")
                end_index = segment.get("end_index")
                formatted_text = segment.get("formatted_text", "")
                title = segment.get("title", "")
                
                if start_index is None or end_index is None:
                    logger.warning(f"段落信息不完整: {segment}")
                    continue
                
                # 确保索引在有效范围内
                start_index = max(0, min(start_index, len(subtitles) - 1))
                end_index = max(start_index, min(end_index, len(subtitles) - 1))
                
                # 移除文本中的索引标记 [0], [1], [2] 等
                if formatted_text:
                    formatted_text = re.sub(r'\[\d+\]\s*', '', formatted_text)
                
                # 如果没有格式化文本，使用原始合并文本
                if not formatted_text:
                    formatted_text = " ".join([subtitles[i]["text"] for i in range(start_index, end_index + 1)])
                
                # 如果没有标题，生成一个简单的标题
                if not title:
                    title = f"第{len(merged_subtitles) + 1}部分"
                
                # 创建合并后的字幕
                merged_subtitle = {
                    "start_time": subtitles[start_index]["start_time"],
                    "end_time": subtitles[end_index]["end_time"],
                    "text": formatted_text,
                    "title": title,
                    "original_indices": list(range(start_index, end_index + 1))
                }
                
                merged_subtitles.append(merged_subtitle)
            
            if not merged_subtitles:
                logger.warning("Ollama没有返回有效的段落，使用方案二")
                return merge_subtitles_by_semantics(subtitles)
                
            logger.info(f"Ollama语义分段完成，共{len(merged_subtitles)}个语义段落")
            return merged_subtitles
            
        except Exception as e:
            logger.error(f"处理Ollama返回的段落时出错: {str(e)}")
            return merge_subtitles_by_semantics(subtitles)
            
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
            
            # 构建提示词
            prompt_template = """请分析以下视频字幕文本，并根据内容的语义连贯性将其分成若干个有意义的段落。
            
字幕文本（每行前面的数字是字幕的索引）：
{text}

要求：
1. 根据内容的语义连贯性和主题变化进行分段，而不是简单地按固定间隔分段
2. 每个段落应该表达一个相对完整的意思或主题
3. 返回JSON格式的结果，包含每个段落的开始和结束字幕索引
4. 对于短视频（不到5分钟），应该生成2-5个段落，不要过度分段
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
            
            # 调用API
            response = client.chat.completions.create(
                model="qwen-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的视频内容分析助手。你的任务是分析视频字幕，并根据语义将其分成有意义的段落。"},
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