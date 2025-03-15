import jieba
import jieba.analyse
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
import logging
import re
import os
from openai import OpenAI

# 直接使用固定的API密钥（与chat_system.py保持一致）
OPENAI_API_KEY = "sk-178e130a121445659860893fdfae1e7d"
OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

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
                'title': generate_title(' '.join([sub['text'] for sub in subtitles])),
                'start_time': subtitles[0]['start_time'],
                'end_time': subtitles[-1]['end_time'],
                'text': format_text_with_punctuation(' '.join([sub['text'] for sub in subtitles])),
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
                'text': format_text_with_punctuation(group['text']),
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

def format_text_with_punctuation(text):
    """
    为文本添加适当的标点符号，优化阅读体验
    """
    if not text:
        return ""
    
    # 替换多个空格为单个空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 首先移除所有现有的标点符号
    clean_text = re.sub(r'[。！？，、；：.!?,;:]', '', text)
    
    # 将文本按空格分割成短语
    phrases = clean_text.split()
    
    # 为每个短语添加标点
    formatted_phrases = []
    
    for i, phrase in enumerate(phrases):
        if i == len(phrases) - 1:  # 最后一个短语
            formatted_phrases.append(phrase + "。")
        else:
            # 根据位置和内容选择标点
            if i % 4 == 0:  # 每4个短语使用一次句号
                formatted_phrases.append(phrase + "。")
            elif i % 4 == 2:  # 每4个短语的第3个使用逗号
                formatted_phrases.append(phrase + "，")
            elif any(phrase.endswith(word) for word in ['吗', '呢', '么']):
                formatted_phrases.append(phrase + "？")
            elif any(phrase.endswith(word) for word in ['啊', '哇', '呀', '哦']):
                formatted_phrases.append(phrase + "！")
            else:
                # 其他情况使用顿号或分号
                if i % 2 == 0:
                    formatted_phrases.append(phrase + "、")
                else:
                    formatted_phrases.append(phrase + "；")
    
    # 连接所有带标点的短语
    formatted_text = " ".join(formatted_phrases)
    
    # 确保最后一个标点是句号
    if not formatted_text.endswith('。') and not formatted_text.endswith('！') and not formatted_text.endswith('？'):
        if formatted_text[-1] in ['，', '、', '；']:
            formatted_text = formatted_text[:-1] + '。'
        else:
            formatted_text = formatted_text + '。'
    
    return formatted_text

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
        prompt = f"""请为以下文本生成一个简短的标题（不超过10个字）：

文本内容：
{text}

要求：
1. 标题应该简洁明了，不超过10个字
2. 标题应该能够准确反映文本的核心内容和主题
3. 不要使用"关于..."、"论..."等形式
4. 直接返回标题，不要有任何解释或其他内容"""
        
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

def generate_title(text, max_words=4):
    """生成标题的主函数，优先使用LLM，失败时回退到传统方法"""
    # 优先使用LLM生成标题
    return generate_title_with_llm(text)