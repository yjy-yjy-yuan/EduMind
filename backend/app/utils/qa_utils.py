"""
问答工具模块
"""
import os
import re
import json
import time
import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Generator
from sentence_transformers import SentenceTransformer
import requests
from dashscope import Generation

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置Ollama API的基础URL
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434/api')

# 检查是否可以使用FAISS
try:
    import faiss
    FAISS_AVAILABLE = True
    print("成功初始化GPU资源")
except ImportError:
    FAISS_AVAILABLE = False
    print("FAISS库不可用，将使用基础向量搜索")

# 检查Ollama服务是否可用
def check_ollama_service():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            logger.info(f"Ollama服务可用，已加载模型: {[model['name'] for model in models]}")
            return True
        else:
            logger.warning(f"Ollama服务返回非200状态码: {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"Ollama服务检查失败: {str(e)}")
        return False

check_ollama_service()

class QASystem:
    def __init__(self, model_name="all-MiniLM-L6-v2"): #初始化问答系统
        """
        Args:model_name: 使用的Sentence Transformer模型名称
        """
        self.model_name = model_name
        self.model = None
        self.index = None
        self.subtitles = []
        self.embeddings = None
        self.is_initialized = False
        
        try:
            logger.info(f"正在加载模型: {model_name}")
            self.model = SentenceTransformer(model_name)
            logger.info(f"模型加载成功: {model_name}")
            self.is_initialized = True
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            self.is_initialized = False
    
    def _create_index(self, dimension): # 创建 FAISS 索引
        """
        Args:dimension: 向量维度
        Returns:FAISS 索引对象
        """
        if FAISS_AVAILABLE:
            try:
                # 尝试使用GPU资源
                res = faiss.StandardGpuResources()
                config = faiss.GpuIndexFlatConfig()
                config.device = 0  # 使用第一个GPU
                index = faiss.GpuIndexFlatIP(res, dimension, config)
                logger.info("成功创建GPU FAISS索引")
                return index
            except Exception as e:
                logger.warning(f"GPU FAISS索引创建失败，回退到CPU: {str(e)}")
                # 回退到CPU版本
                index = faiss.IndexFlatIP(dimension)
                logger.info("成功创建CPU FAISS索引")
                return index
        else:
            # 如果FAISS不可用，返回None
            logger.warning("FAISS不可用，将使用基础向量搜索")
            return None
    
    """解析时间戳字符串，返回开始和结束时间"""
    def _parse_timestamp(self, timestamp_str: str) -> Tuple[float, float]:
        parts = timestamp_str.split(' --> ')
        start_time = self._time_to_seconds(parts[0])
        end_time = self._time_to_seconds(parts[1])
        return start_time, end_time
    
    # 从字幕文件创建知识库
    def create_knowledge_base(self, subtitle_path):
        """
        Args:subtitle_path: 字幕文件路径
        Returns:bool: 是否成功创建知识库
        """
        if not self.is_initialized:
            logger.error("模型未初始化，无法创建知识库")
            return False
        
        try:
            # 读取字幕文件
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析SRT格式字幕
            subtitle_blocks = re.split(r'\n\s*\n', content.strip())
            subtitles = []
            
            for block in subtitle_blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    try:
                        index = int(lines[0])
                        timestamp = lines[1]
                        text = ' '.join(lines[2:])
                        
                        start_time, end_time = self._parse_timestamp(timestamp)
                        
                        subtitles.append({
                            'index': index,
                            'start_time': start_time,
                            'end_time': end_time,
                            'text': text
                        })
                    except Exception as e:
                        logger.warning(f"解析字幕块失败: {block}, 错误: {str(e)}")
                        continue
            
            # 按时间排序
            subtitles.sort(key=lambda x: x['start_time'])
            
            # 合并相邻的字幕，如果它们之间的间隔小于1秒
            merged_subtitles = []
            current_subtitle = None
            
            for subtitle in subtitles:
                if current_subtitle is None:
                    current_subtitle = subtitle.copy()
                elif subtitle['start_time'] - current_subtitle['end_time'] < 1.0:
                    # 合并字幕
                    current_subtitle['end_time'] = subtitle['end_time']
                    current_subtitle['text'] += ' ' + subtitle['text']
                else:
                    # 添加当前字幕并开始新的字幕
                    merged_subtitles.append(current_subtitle)
                    current_subtitle = subtitle.copy()
            
            # 添加最后一个字幕
            if current_subtitle is not None:
                merged_subtitles.append(current_subtitle)
            
            # 更新字幕列表
            self.subtitles = merged_subtitles
            
            # 提取文本并创建嵌入
            texts = [subtitle['text'] for subtitle in self.subtitles]
            self.embeddings = self.model.encode(texts)
            
            # 创建索引
            if FAISS_AVAILABLE:
                dimension = self.embeddings.shape[1]
                self.index = self._create_index(dimension)
                if self.index is not None:
                    self.index.add(self.embeddings)
                    logger.info(f"成功创建FAISS索引，包含{len(texts)}个字幕片段")
            
            logger.info(f"成功创建知识库，包含{len(self.subtitles)}个字幕片段")
            return True
        
        except Exception as e:
            logger.error(f"创建知识库失败: {str(e)}")
            return False
    
    """将时间字符串转换为秒数"""
    def _time_to_seconds(self, time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    
    # 搜索与查询最相似的片段
    def search_similar_segments(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Args:
            query: 查询文本
            top_k: 返回的结果数量
        Returns:List[Dict]: 相似片段列表
        """
        if not self.is_initialized or len(self.subtitles) == 0:
            logger.error("模型未初始化或知识库为空")
            return []
        
        try:
            # 编码查询
            query_embedding = self.model.encode([query])[0]
            
            if FAISS_AVAILABLE and self.index is not None:
                # 使用FAISS搜索
                scores, indices = self.index.search(np.array([query_embedding]), top_k)
                results = []
                
                for i, idx in enumerate(indices[0]):
                    if idx < len(self.subtitles) and idx >= 0:
                        subtitle = self.subtitles[idx]
                        results.append({
                            'text': subtitle['text'],
                            'start_time': subtitle['start_time'],
                            'end_time': subtitle['end_time'],
                            'score': float(scores[0][i])
                        })
                
                return results
            else:
                # 使用基础向量搜索
                similarities = np.dot(self.embeddings, query_embedding)
                top_indices = np.argsort(similarities)[-top_k:][::-1]
                
                results = []
                for idx in top_indices:
                    subtitle = self.subtitles[idx]
                    results.append({
                        'text': subtitle['text'],
                        'start_time': subtitle['start_time'],
                        'end_time': subtitle['end_time'],
                        'score': float(similarities[idx])
                    })
                
                return results
        
        except Exception as e:
            logger.error(f"搜索相似片段失败: {str(e)}")
            return []
    
    # 获取问题的答案(非流式)
    def get_answer(self, question: str, api_key: str = None, mode: str = 'video', use_ollama: bool = False, deep_thinking: bool = False):
        """        
        Args:
            question: 用户问题
            api_key: 阿里云API密钥
            mode: 问答模式，'video'或'free'
            use_ollama: 是否使用本地Ollama服务
            deep_thinking: 是否启用深度思考模式
        
        Returns:
            str: 问题的答案
        """
        try:
            if use_ollama:
                # 使用本地Ollama服务
                return self.get_answer_ollama(question, mode, None, deep_thinking)
            else:
                # 使用在线API
                return self.get_answer_online(question, api_key, mode, None, deep_thinking)
        
        except Exception as e:
            logger.error(f"获取答案失败: {str(e)}")
            return f"获取答案时出错: {str(e)}"
    
    # 获取问题的答案（流式响应）
    def get_answer_stream(self, question: str, api_key: str, mode: str = 'video', context: str = None, use_ollama: bool = False, deep_thinking: bool = False):
        """
        Args:
            question: 用户问题
            api_key: 阿里云API密钥
            mode: 问答模式，'video'或'free'
            context: 可选的上下文信息
            use_ollama: 是否使用本地Ollama服务
            deep_thinking: 是否启用深度思考模式
        
        Yields:
            str: 问题答案的流式响应
        """
        try:
            if use_ollama:
                # 使用本地Ollama服务
                yield from self.get_answer_stream_ollama(question, mode, context, deep_thinking)
            else:
                # 使用在线API
                yield from self.get_answer_stream_online(question, api_key, mode, context, deep_thinking)
        
        except Exception as e:
            logger.error(f"流式获取答案失败: {str(e)}")
            yield f"获取答案时出错: {str(e)}"
    
    # 使用在线API获取问题的答案（非流式）
    def get_answer_online(self, question: str, api_key: str = "sk-59a6a7690bfb42cd887365795e114002", mode: str = 'video', context: str = None, deep_thinking: bool = False):
        """
        Args:
            question: 用户问题
            api_key: 阿里云API密钥，默认使用固定值
            mode: 问答模式，'video'或'free'
            context: 可选的上下文信息
            deep_thinking: 是否启用深度思考模式
        
        Returns:
            str: 问题的答案
        """
        try:
            if mode == 'video' and not context:
                if not self.is_initialized or len(self.subtitles) == 0:
                    return "视频知识库未初始化，请先上传视频并等待处理完成"
                
                # 搜索相关片段
                segments = self.search_similar_segments(question, top_k=3)
                
                if not segments:
                    return "未找到与问题相关的视频内容"
                
                # 构建上下文
                context = "\n\n".join([f"片段 {i+1}（{self._format_time(seg['start_time'])} - {self._format_time(seg['end_time'])}）: {seg['text']}" 
                                    for i, seg in enumerate(segments)])
            
            # 构建提示词
            prompt = f"""你是一个教育助手。请回答用户的问题。

用户问题: {question}

请提供有帮助的回答。如果你不确定答案，请诚实地说明。"""
            
            if mode == 'video':
                prompt = f"""你是一个教育视频内容助手。请根据以下视频内容片段回答用户的问题。
                
视频内容片段:
{context}

用户问题: {question}

请根据提供的视频内容片段回答问题。如果视频内容中没有足够的信息来回答问题，请说明这一点。"""
            
            logger.info(f"构建的提示词: {prompt[:100]}...")
            
            # 根据深度思考模式选择不同的模型和处理方式
            if deep_thinking:
                # 深度思考模式使用 deepseek-r1
                model_to_use = "deepseek-r1"
                # 在用户输入前添加"深度思考"指令
                modified_prompt = f"深度思考\n{prompt}"
                logger.info(f"使用在线深度思考模式，选择模型: {model_to_use}")
            else:
                # 普通模式使用 qwen-turbo
                model_to_use = "qwen-turbo"
                modified_prompt = prompt
                logger.info(f"使用在线普通模式，选择模型: {model_to_use}")
            
            # 调用API获取回答
            response = Generation.call(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": "你是一个教育助手，请始终使用中文回答问题。"},
                    {"role": "user", "content": modified_prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                api_key=api_key,
                timeout=60  # 设置60秒超时
            )
            
            if response.status_code != 200:
                logger.error(f"API请求失败: {response.status_code}, {response.message}")
                return f"API请求失败: {response.status_code}, {response.message}"
            
            # 提取文本，处理不同的响应格式
            answer = ""
            
            # 格式1: choices[0].message.content 格式
            if (hasattr(response, 'output') and response.output is not None and 
                hasattr(response.output, 'choices') and response.output.choices is not None and 
                len(response.output.choices) > 0 and 
                hasattr(response.output.choices[0], 'message') and 
                hasattr(response.output.choices[0].message, 'content')):
                answer = response.output.choices[0].message.content
                logger.info(f"使用choices格式提取文本: {answer[:20]}...")
            
            # 格式2: text 格式
            elif hasattr(response, 'text') and response.text is not None:
                answer = response.text
                logger.info(f"使用text格式提取文本: {answer[:20]}...")
            
            # 格式3: output.text 格式
            elif (hasattr(response, 'output') and response.output is not None and 
                  hasattr(response.output, 'text') and response.output.text is not None):
                answer = response.output.text
                logger.info(f"使用output.text格式提取文本: {answer[:20]}...")
            
            # 如果无法提取文本，返回错误
            else:
                logger.error(f"无法从响应中提取文本: {response}")
                return "API响应格式错误：无法提取回答文本"
            
            # 如果是深度思考模式，处理回答格式
            if deep_thinking:
                # 提取思考过程和最终答案
                think_matches = re.findall(r'<think>(.*?)</think>', answer, re.DOTALL)
                if think_matches:
                    # 合并所有思考过程
                    thinking_process = "\n\n".join([match.strip() for match in think_matches])
                    # 移除所有思考标签及其内容
                    final_answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
                    
                    # 格式化为HTML，使思考过程可折叠
                    formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                    return self._format_answer(formatted_answer)
                else:
                    # 检查是否使用了其他格式的思考过程
                    # 例如：1. 在分析这个问题时... 2. 这个问题可能... 3. 我需要确保...
                    numbered_format = re.findall(r'(\d+\.\s+[^0-9]+?)(?=\d+\.|$)', answer, re.DOTALL)
                    if numbered_format and len(numbered_format) >= 3:
                        # 提取前面的思考部分（前n-1项）
                        thinking_parts = numbered_format[:-1]
                        thinking_process = "\n\n".join([part.strip() for part in thinking_parts])
                        
                        # 最后一项可能是最终答案
                        final_answer = numbered_format[-1].strip()
                        
                        # 如果最后一项包含"最终答案"或类似字样
                        final_answer_match = re.search(r'(?:最终答案[：:]\s*|最后答案[：:]\s*)(.*?)$', final_answer, re.DOTALL)
                        if final_answer_match:
                            final_answer = final_answer_match.group(1).strip()
                        
                        # 格式化为HTML，使思考过程可折叠
                        formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                        return self._format_answer(formatted_answer)
                    
                    # 检查是否使用了其他格式的思考过程
                    # 例如：1. **分析问题**：... 2. **思考过程**：... 3. **解决方案**：...
                    analysis_match = re.search(r'(?:1\.?\s*\*\*分析问题\*\*：|分析问题：)(.*?)(?:2\.|\*\*思考|$)', answer, re.DOTALL)
                    thinking_match = re.search(r'(?:2\.?\s*\*\*思考过程\*\*：|思考过程：)(.*?)(?:3\.|\*\*解决|$)', answer, re.DOTALL)
                    solution_match = re.search(r'(?:3\.?\s*\*\*解决方案\*\*：|解决方案：)(.*?)(?:最终答案|$)', answer, re.DOTALL)
                    
                    if analysis_match or thinking_match or solution_match:
                        # 提取思考部分
                        thinking_parts = []
                        if analysis_match:
                            thinking_parts.append(f"**分析问题**：{analysis_match.group(1).strip()}")
                        if thinking_match:
                            thinking_parts.append(f"**思考过程**：{thinking_match.group(1).strip()}")
                        if solution_match:
                            thinking_parts.append(f"**解决方案**：{solution_match.group(1).strip()}")
                        
                        thinking_process = "\n\n".join(thinking_parts)
                        
                        # 提取最终答案
                        final_answer_match = re.search(r'(?:最终答案：|最终答案:|最终答案|最后答案：|最后答案:|最后答案)(.*?)$', answer, re.DOTALL)
                        if final_answer_match:
                            final_answer = final_answer_match.group(1).strip()
                        else:
                            # 如果没有明确的最终答案标记，尝试提取最后一段作为答案
                            paragraphs = answer.split('\n\n')
                            final_answer = paragraphs[-1].strip()
                            # 如果最后一段包含分析/思考/解决方案，则使用一个通用回答
                            if re.search(r'分析|思考|解决方案', final_answer):
                                final_answer = "根据以上分析，我的回答是：" + re.sub(r'.*?(您好|你好).*', '您好！我是教育助手，请问有什么可以帮助您的？', answer)
                        
                        # 格式化为HTML，使思考过程可折叠
                        formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                        return self._format_answer(formatted_answer)
                    
                    # 如果没有找到思考标签，可能是模型没有按照指令生成思考过程
                    # 在这种情况下，我们生成一个通用的思考过程
                    logger.warning("深度思考模式下未找到标准思考格式，生成通用思考过程")
                    
                    # 提取问题
                    question_text = ""
                    try:
                        question_text = prompt.split('用户问题: ')[1].split('\n')[0]
                    except:
                        question_text = "未能提取到具体问题"
                    
                    thinking_process = f"""**分析问题**："{question_text}"

首先，我需要仔细理解用户提出的问题，确定问题的核心要点和用户的真实需求。这个问题可能涉及到视频内容分析、概念解释、知识点梳理或其他教育相关主题。

**思考过程**：
1. 我需要回顾视频中提到的关键信息和核心概念
2. 分析这些概念之间的逻辑关系和层次结构
3. 考虑不同角度的解释和可能的应用场景
4. 整合相关的背景知识和上下文信息
5. 确保回答的准确性、全面性和教育价值

**解决方案**：
基于以上分析，我将提供一个结构清晰、内容准确的回答，帮助用户深入理解相关知识点。我会关注回答的教育意义，确保信息的可靠性，并尽可能提供有价值的延伸思考。"""
                    
                    formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{answer}"""
                    return self._format_answer(formatted_answer)
            
            return self._format_answer(answer)
        
        except Exception as e:
            logger.error(f"获取在线答案失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return f"获取答案时出错: {str(e)}"
    
    # 使用在线API获取问题的答案（流式响应）
    def get_answer_stream_online(self, question: str, api_key: str = "sk-59a6a7690bfb42cd887365795e114002", mode: str = 'video', context: str = None, deep_thinking: bool = False):
        """
        Args:
            question: 用户问题
            api_key: 阿里云API密钥，默认使用固定值
            mode: 问答模式，'video'或'free'
            context: 可选的上下文信息
            deep_thinking: 是否启用深度思考模式
        
        Yields:
            str: 问题答案的流式响应
        """
        try:
            # 标记是否已经输出了格式化回答
            formatted_answer_yielded = False
            
            if mode == 'video' and not context:
                if not self.is_initialized or len(self.subtitles) == 0:
                    yield "视频知识库未初始化，请先上传视频并等待处理完成"
                    return
                
                # 搜索相关片段
                segments = self.search_similar_segments(question, top_k=3)
                
                if not segments:
                    yield "未找到与问题相关的视频内容"
                    return
                
                # 构建上下文
                context = "\n\n".join([f"片段 {i+1}（{self._format_time(seg['start_time'])} - {self._format_time(seg['end_time'])}）: {seg['text']}" 
                                    for i, seg in enumerate(segments)])
            
            # 构建提示词
            prompt = f"""你是一个教育助手。请回答用户的问题。

用户问题: {question}

请提供有帮助的回答。如果你不确定答案，请诚实地说明。"""
            
            if mode == 'video':
                prompt = f"""你是一个教育视频内容助手。请根据以下视频内容片段回答用户的问题。
                
视频内容片段:
{context}

用户问题: {question}

请根据提供的视频内容片段回答问题。如果视频内容中没有足够的信息来回答问题，请说明这一点。"""
            
            logger.info(f"构建的提示词: {prompt[:100]}...")
            
            # 根据深度思考模式选择不同的模型和处理方式
            if deep_thinking:
                # 深度思考模式使用 deepseek-r1
                model_to_use = "deepseek-r1"
                # 在用户输入前添加"深度思考"指令
                modified_prompt = f"深度思考\n{prompt}"
                logger.info(f"使用在线深度思考模式，选择模型: {model_to_use}")
            else:
                # 普通模式使用 qwen-turbo
                model_to_use = "qwen-turbo"
                modified_prompt = prompt
                logger.info(f"使用在线普通模式，选择模型: {model_to_use}")
            
            # 创建一个缓冲区来收集完整的响应
            complete_response = ""
            
            # 标记是否已经有响应
            has_yielded = False
            
            # 处理API调用和响应
            try:
                # 不使用流式模式，直接获取完整回答
                # 这样可以避免文本不连贯的问题
                if not deep_thinking:
                    # 非深度思考模式，直接获取完整回答
                    logger.info("使用非流式模式获取完整回答")
                    response = Generation.call(
                        model=model_to_use,
                        messages=[
                            {"role": "system", "content": "你是一个教育助手，请始终使用中文回答问题。"},
                            {"role": "user", "content": modified_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1000,
                        api_key=api_key,
                        stream=False,  # 不使用流式模式
                        timeout=60  # 设置60秒超时
                    )
                    
                    if response.status_code == 200:
                        try:
                            # 提取文本
                            if 'output' in response and 'text' in response.output and response.output.text is not None:
                                answer_text = response.output.text
                                logger.info(f"获取到完整回答: {answer_text[:50]}...")
                            elif ('output' in response and 'choices' in response.output and 
                                  response.output.choices is not None and 
                                  len(response.output.choices) > 0 and 
                                  'message' in response.output.choices[0] and 
                                  'content' in response.output.choices[0].message):
                                answer_text = response.output.choices[0].message.content
                                logger.info(f"获取到完整回答(choices格式): {answer_text[:50]}...")
                            else:
                                logger.error(f"无法从响应中提取文本: {response}")
                                yield "无法从API响应中提取文本，请稍后重试。"
                                return
                            
                            # 先格式化完整答案
                            formatted_answer = self._format_answer(answer_text)
                            # 然后分块输出已格式化的答案
                            chunk_size = 10  # 每次输出10个字符
                            for i in range(0, len(formatted_answer), chunk_size):
                                chunk = formatted_answer[i:i+chunk_size]
                                yield chunk
                                # 添加一个小延迟，模拟流式效果
                                import time
                                time.sleep(0.05)  # 50毫秒延迟
                            
                            has_yielded = True
                            complete_response = answer_text
                            
                        except Exception as e:
                            logger.error(f"处理响应数据时出错: {str(e)}")
                            import traceback
                            logger.error(traceback.format_exc())
                            yield f"处理响应数据时出错: {str(e)}"
                            return
                    else:
                        logger.error(f"API请求失败: {response.status_code}, {response.message}")
                        yield f"API请求失败: {response.status_code}, {response.message}"
                        return
                else:
                    # 深度思考模式仍然使用流式响应，因为需要处理思考过程
                    # 但是我们会收集完整的响应后再处理
                    logger.info("深度思考模式使用流式响应")
                    full_response = ""
                    thinking_process = ""  # 初始化为空字符串
                    final_answer = ""
                    
                    # 用于存储最后一个完整的响应对象
                    last_complete_response = None
                    
                    for response in Generation.call(
                        model=model_to_use,
                        messages=[
                            {"role": "system", "content": "你是一个教育助手，请始终使用中文回答问题。"},
                            {"role": "user", "content": modified_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1000,
                        api_key=api_key,
                        stream=True,
                        incremental_output=True,
                        batch_size=20,
                        timeout=60  # 设置60秒超时
                    ):
                        if response.status_code == 200:
                            try:
                                # 将响应转换为字符串并解析JSON
                                response_str = str(response)
                                logger.debug(f"响应对象字符串: {response_str[:200]}...")
                                
                                # 使用正则表达式提取JSON部分
                                import re
                                import json
                                
                                # 解析JSON响应
                                json_obj = None
                                try:
                                    # 尝试直接解析整个响应字符串
                                    json_obj = json.loads(response_str)
                                except Exception as e:
                                    logger.error(f"解析JSON对象失败: {str(e)}")
                                    
                                    # 如果整个字符串不是有效的JSON，尝试提取JSON部分
                                    json_match = re.search(r'({.*})', response_str)
                                    if json_match:
                                        try:
                                            json_str = json_match.group(1)
                                            json_obj = json.loads(json_str)
                                        except Exception as e:
                                            logger.error(f"解析JSON字符串失败: {str(e)}")
                                
                                # 如果成功解析了JSON
                                if json_obj:
                                    # 保存最后一个完整的响应对象
                                    last_complete_response = json_obj
                                    
                                    # 提取文本内容
                                    current_text = ""
                                    
                                    # 检查不同的响应格式
                                    if 'output' in json_obj and 'text' in json_obj['output'] and json_obj['output']['text'] is not None:
                                        current_text = json_obj['output']['text']
                                    elif ('output' in json_obj and 'choices' in json_obj['output'] and 
                                          json_obj['output']['choices'] is not None and 
                                          len(json_obj['output']['choices']) > 0 and 
                                          'message' in json_obj['output']['choices'][0] and 
                                          'content' in json_obj['output']['choices'][0]['message']):
                                        current_text = json_obj['output']['choices'][0]['message']['content']
                                        
                                        # 如果有reasoning_content，记录下来
                                        if 'reasoning_content' in json_obj['output']['choices'][0]['message']:
                                            current_thinking = json_obj['output']['choices'][0]['message']['reasoning_content']
                                            if current_thinking:
                                                thinking_process += current_thinking  # 累积思考过程
                                                logger.info(f"找到思考过程: {current_thinking[:50]}...")
                                
                                    # 将当前文本添加到完整响应
                                    if current_text:
                                        full_response += current_text
                                    
                                    # 检查是否有finish_reason为stop的信号
                                    finish_reason = None
                                    try:
                                        if 'output' in json_obj and 'finish_reason' in json_obj['output']:
                                            finish_reason = json_obj['output']['finish_reason']
                                        elif ('output' in json_obj and 'choices' in json_obj['output'] and 
                                              json_obj['output']['choices'] is not None and 
                                              len(json_obj['output']['choices']) > 0 and 
                                              'finish_reason' in json_obj['output']['choices'][0]):
                                            finish_reason = json_obj['output']['choices'][0]['finish_reason']
                                    except:
                                        pass
                                    
                                    # 为了提供一些反馈，可以输出一个点
                                    if not has_yielded:
                                        yield "思考中..."
                                        has_yielded = True
                                    
                                    # 如果是最后一个响应块，保存最终答案
                                    if finish_reason == "stop":
                                        final_answer = full_response
                                        logger.info("API响应完成，收到停止信号")
                            
                            except Exception as e:
                                logger.error(f"处理响应数据时出错: {str(e)}")
                                continue
                        else:
                            logger.error(f"API请求失败: {response.status_code}, {response.message}")
                            yield f"API请求失败: {response.status_code}, {response.message}"
                            return
                    
                    # 处理完整的响应
                    complete_response = full_response
                    
                    # 从最后一个完整响应中提取reasoning_content
                    if last_complete_response:
                        try:
                            if ('output' in last_complete_response and 
                                'choices' in last_complete_response['output'] and 
                                last_complete_response['output']['choices'] is not None and 
                                len(last_complete_response['output']['choices']) > 0 and 
                                'message' in last_complete_response['output']['choices'][0] and 
                                'reasoning_content' in last_complete_response['output']['choices'][0]['message']):
                                
                                api_thinking_process = last_complete_response['output']['choices'][0]['message']['reasoning_content']
                                if api_thinking_process and len(api_thinking_process) > 20:
                                    thinking_process += api_thinking_process  # 累积思考过程
                                    logger.info(f"从最后一个响应中提取到思考过程，长度={len(thinking_process)}")
                                    
                                    # 从同一响应中提取content作为最终答案
                                    if 'content' in last_complete_response['output']['choices'][0]['message']:
                                        api_content = last_complete_response['output']['choices'][0]['message']['content']
                                        if api_content and len(api_content) > 10:
                                            final_answer = api_content
                                            logger.info(f"从最后一个响应中提取到最终答案，长度={len(final_answer)}")
                        except Exception as e:
                            logger.error(f"从最后一个响应中提取思考过程和答案时出错: {str(e)}")
                            import traceback
                            logger.error(traceback.format_exc())
                    
                    # 如果思考过程为空或太短，尝试从完整响应中提取
                    if not thinking_process or len(thinking_process) < 20:
                        logger.warning(f"思考过程为空或太短({len(thinking_process) if thinking_process else 0}个字符)，尝试从完整响应中提取")
                        
                        # 尝试从完整响应中提取思考过程
                        # 方法1：寻找<think>标签
                        think_matches = re.findall(r'<think>(.*?)</think>', complete_response, re.DOTALL)
                        if think_matches:
                            thinking_process = "\n\n".join([match.strip() for match in think_matches])
                            # 移除所有思考标签及其内容
                            final_answer = re.sub(r'<think>.*?</think>', '', complete_response, flags=re.DOTALL).strip()
                            logger.info(f"从<think>标签中提取到思考过程，长度={len(thinking_process)}")
                        else:
                            # 方法2：尝试提取"思考过程："部分
                            thinking_match = re.search(r'(思考过程[：:](.*?))(回答[：:]|最终答案[：:]|$)', complete_response, re.DOTALL)
                            if thinking_match:
                                thinking_process = thinking_match.group(2).strip()
                                # 尝试提取最终答案
                                answer_match = re.search(r'(回答[：:]|最终答案[：:])(.*?)$', complete_response, re.DOTALL)
                                if answer_match:
                                    final_answer = answer_match.group(2).strip()
                                else:
                                    final_answer = complete_response
                                logger.info(f"从'思考过程:'部分提取到思考过程，长度={len(thinking_process)}")
                            else:
                                # 方法3：尝试提取"分析："部分
                                analysis_match = re.search(r'(分析[：:](.*?))(解答[：:]|回答[：:]|$)', complete_response, re.DOTALL)
                                if analysis_match:
                                    thinking_process = analysis_match.group(2).strip()
                                    # 尝试提取最终答案
                                    answer_match = re.search(r'(解答[：:]|回答[：:])(.*?)$', complete_response, re.DOTALL)
                                    if answer_match:
                                        final_answer = answer_match.group(2).strip()
                                    else:
                                        final_answer = complete_response
                                    logger.info(f"从'分析:'部分提取到思考过程，长度={len(thinking_process)}")
                                else:
                                    # 如果仍然无法提取，使用模型提供的思考过程
                                    logger.warning("深度思考模式下未找到标准思考格式，使用模型提供的思考过程")
                                    
                                    # 使用一个更简短的通用思考过程
                                    thinking_process = f"""我分析了用户的问题"{question}"，并考虑了如何提供最有帮助的回答。"""
                
                    # 如果最终答案为空或太短，使用完整响应
                    if not final_answer or len(final_answer) < 10:
                        final_answer = complete_response or "你好！我是教育助手，很高兴为您提供帮助。请问有什么我可以帮您解答的问题吗？"
                        logger.warning(f"最终答案为空或太短，使用完整响应，长度={len(final_answer)}")
                    
                    # 确保思考过程不为空
                    if not thinking_process:
                        thinking_process = "我分析了您的问题，并思考了如何提供最有帮助的回答。"
                        logger.warning("思考过程为空，使用默认思考过程")
                    
                    # 格式化为HTML，使思考过程可折叠
                    formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                    
                    logger.info(f"返回格式化回答，思考过程长度={len(thinking_process)}，最终答案长度={len(final_answer)}")
                    # 清除"思考中..."的提示，先发送一个空字符串
                    if has_yielded and deep_thinking:
                        yield ""
                    yield self._format_answer(formatted_answer)
                    formatted_answer_yielded = True
                    
                    logger.info("API响应处理完成")
            except Exception as e:
                logger.error(f"DashScope API调用失败: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                yield f"API调用失败: {str(e)}。请检查API密钥是否有效，或者网络连接是否正常。"
                return
            
            # 处理深度思考模式的回答
            if deep_thinking and has_yielded and not formatted_answer_yielded:
                # 提取思考过程和最终答案
                think_matches = re.findall(r'<think>(.*?)</think>', complete_response, re.DOTALL)
                if think_matches:
                    # 合并所有思考过程，如果thinking_process已经有内容，则添加到现有内容中
                    if thinking_process:
                        thinking_process += "\n\n" + "\n\n".join([match.strip() for match in think_matches])
                    else:
                        thinking_process = "\n\n".join([match.strip() for match in think_matches])
                    # 移除所有思考标签及其内容
                    final_answer = re.sub(r'<think>.*?</think>', '', complete_response, flags=re.DOTALL).strip()
                    
                    # 格式化为HTML，使思考过程可折叠
                    formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                    yield self._format_answer(formatted_answer)
                    formatted_answer_yielded = True
                    return
                
                # 检查是否使用了其他格式的思考过程
                # 例如：1. 在分析这个问题时... 2. 这个问题可能... 3. 我需要确保...
                numbered_format = re.findall(r'(\d+\.\s+[^0-9]+?)(?=\d+\.|$)', complete_response, re.DOTALL)
                if numbered_format and len(numbered_format) >= 3:
                    # 提取前面的思考部分（前n-1项）
                    thinking_parts = numbered_format[:-1]
                    thinking_process = "\n\n".join([part.strip() for part in thinking_parts])
                    
                    # 最后一项可能是最终答案
                    final_answer = numbered_format[-1].strip()
                    
                    # 如果最后一项包含"最终答案"或类似字样
                    final_answer_match = re.search(r'(?:最终答案[：:]\s*|最后答案[：:]\s*)(.*?)$', final_answer, re.DOTALL)
                    if final_answer_match:
                        final_answer = final_answer_match.group(1).strip()
                    
                    # 格式化为HTML，使思考过程可折叠
                    formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                    yield self._format_answer(formatted_answer)
                    formatted_answer_yielded = True
                    return
                
                # 检查是否使用了其他格式的思考过程
                # 例如：1. **分析问题**：... 2. **思考过程**：... 3. **解决方案**：...
                analysis_match = re.search(r'(?:1\.?\s*\*\*分析问题\*\*：|分析问题：)(.*?)(?:2\.|\*\*思考|$)', complete_response, re.DOTALL)
                thinking_match = re.search(r'(?:2\.?\s*\*\*思考过程\*\*：|思考过程：)(.*?)(?:3\.|\*\*解决|$)', complete_response, re.DOTALL)
                solution_match = re.search(r'(?:3\.?\s*\*\*解决方案\*\*：|解决方案：)(.*?)(?:最终答案|$)', complete_response, re.DOTALL)
                
                if analysis_match or thinking_match or solution_match:
                    # 提取思考部分
                    thinking_parts = []
                    if analysis_match:
                        thinking_parts.append(f"**分析问题**：{analysis_match.group(1).strip()}")
                    if thinking_match:
                        thinking_parts.append(f"**思考过程**：{thinking_match.group(1).strip()}")
                    if solution_match:
                        thinking_parts.append(f"**解决方案**：{solution_match.group(1).strip()}")
                    
                    thinking_process = "\n\n".join(thinking_parts)
                    
                    # 提取最终答案
                    final_answer_match = re.search(r'(?:最终答案：|最终答案:|最终答案|最后答案：|最后答案:|最后答案)(.*?)$', complete_response, re.DOTALL)
                    if final_answer_match:
                        final_answer = final_answer_match.group(1).strip()
                    else:
                        # 如果没有明确的最终答案标记，尝试提取最后一段作为答案
                        paragraphs = complete_response.split('\n\n')
                        final_answer = paragraphs[-1].strip()
                        # 如果最后一段包含分析/思考/解决方案，则使用一个通用回答
                        if re.search(r'分析|思考|解决方案', final_answer):
                            final_answer = "根据以上分析，我的回答是：" + re.sub(r'.*?(您好|你好).*', '您好！我是教育助手，请问有什么可以帮助您的？', complete_response)
                    
                    # 格式化为HTML，使思考过程可折叠
                    formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                    yield self._format_answer(formatted_answer)
                    formatted_answer_yielded = True
                    return
                
                # 如果没有找到思考标签，可能是模型没有按照指令生成思考过程
                # 在这种情况下，我们生成一个通用的思考过程
                if not formatted_answer_yielded:
                    logger.warning("深度思考模式下未找到标准思考格式，生成通用思考过程")
                    
                    # 提取问题
                    question_text = ""
                    try:
                        question_text = prompt.split('用户问题: ')[1].split('\n')[0]
                    except:
                        question_text = "未能提取到具体问题"
                    
                    thinking_process = f"""**分析问题**："{question_text}"

首先，我需要仔细理解用户提出的问题，确定问题的核心要点和用户的真实需求。这个问题可能涉及到视频内容分析、概念解释、知识点梳理或其他教育相关主题。

**思考过程**：
1. 我需要回顾视频中提到的关键信息和核心概念
2. 分析这些概念之间的逻辑关系和层次结构
3. 考虑不同角度的解释和可能的应用场景
4. 整合相关的背景知识和上下文信息
5. 确保回答的准确性、全面性和教育价值

**解决方案**：
基于以上分析，我将提供一个结构清晰、内容准确的回答，帮助用户深入理解相关知识点。我会关注回答的教育意义，确保信息的可靠性，并尽可能提供有价值的延伸思考。"""
                    
                    formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{complete_response}"""
                    yield self._format_answer(formatted_answer)
                    formatted_answer_yielded = True
            
            # 如果没有收到任何响应，返回一个默认回答
            if not has_yielded:
                logger.warning("未收到API任何响应，返回默认回答")
                yield "我是AI助手，很抱歉，我目前无法处理您的请求。这可能是因为API服务暂时不可用。请稍后再试或联系管理员。"
                
        except requests.exceptions.Timeout:
            logger.error("API请求超时")
            yield "API请求超时。请检查API服务是否正常运行，或尝试使用在线模式。"
            return
        except requests.exceptions.ConnectionError:
            logger.error("无法连接到API服务")
            yield "无法连接到API服务。请确保API服务正在运行，或尝试使用在线模式。"
            return
        except Exception as e:
            logger.error(f"获取流式在线答案失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            yield f"获取答案时出错: {str(e)}"
    
    # 使用Ollama获取问题的答案（非流式）
    def get_answer_ollama(self, question: str, mode: str = 'video', context: str = None, deep_thinking: bool = False):
        """
        Args:
            question: 用户问题
            mode: 问答模式，'video'或'free'
            context: 可选的上下文信息
            deep_thinking: 是否启用深度思考模式
        
        Returns:
            str: 问题的答案
        """
        import requests
        
        try:
            if mode == 'video' and not context:
                if not self.is_initialized or len(self.subtitles) == 0:
                    return "视频知识库未初始化，请先上传视频并等待处理完成"
                
                # 搜索相关片段
                segments = self.search_similar_segments(question, top_k=3)
                
                if not segments:
                    return "未找到与问题相关的视频内容"
                
                # 构建上下文
                context = "\n\n".join([f"片段 {i+1}（{self._format_time(seg['start_time'])} - {self._format_time(seg['end_time'])}）: {seg['text']}" 
                                    for i, seg in enumerate(segments)])
            
            # 构建提示词
            prompt = f"""你是一个教育助手。请回答用户的问题。

用户问题: {question}

请提供有帮助的回答。如果你不确定答案，请诚实地说明。"""
            
            # 离线下，基于视频内容的问答模式(非流式)
            if mode == 'video':
                prompt = f"""你是一个教育视频内容助手。请根据以下视频内容片段回答用户的问题。
                
视频内容片段:
{context}

用户问题: {question}

请根据提供的视频内容片段回答问题。如果视频内容中没有足够的信息来回答问题，请说明这一点。"""
            
            logger.info(f"构建的提示词: {prompt[:100]}...")
            
            # 根据深度思考模式调整系统提示词
            system_prompt = "你是一个教育助手，请始终使用中文回答问题。"
            
            # 离线下，基于视频内容的问答模式(深度思考)
            if deep_thinking:
                system_prompt += """你必须按照以下格式回答：
1. 首先，在<think>标签内详细分析问题并展示你的思考过程
2. 然后，在标签外给出最终答案

例如：
<think>
首先，我需要理解问题的核心...
分析可能的解决方案...
考虑各种因素...
</think>

基于以上思考，我的回答是...

这个格式是强制性的，你必须将所有思考过程放在<think>标签内。
不要在回答中介绍自己，直接回答问题。"""
            else:
                system_prompt += "请直接给出简洁明了的回答，无需展示思考过程。"
            
            # 离线模式下根据深度思考模式选择不同的模型
            if deep_thinking:
                model_to_use = "deepseek-r1:8b"  # 深度思考模式使用 deepseek-r1:8b
                logger.info(f"使用深度思考模式，选择模型: {model_to_use}")
            else:
                model_to_use = "qwen3:8b"  # 普通模式使用 qwen2.5:7b
                logger.info(f"使用普通模式，选择模型: {model_to_use}")
            
            # 构建请求
            payload = {
                "model": model_to_use,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False
            }
            
            # 发送请求到Ollama API
            response = requests.post(
                f"{OLLAMA_BASE_URL}/generate", 
                json=payload,
                timeout=60  # 设置60秒超时
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if 'response' in response_data:
                    answer = response_data['response']
                    
                    # 处理深度思考模式的回答
                    if deep_thinking:
                        # 提取思考过程和最终答案
                        think_matches = re.findall(r'<think>(.*?)</think>', answer, re.DOTALL)
                        if think_matches:
                            # 合并所有思考过程
                            thinking_process = "\n\n".join([match.strip() for match in think_matches])
                            # 移除所有思考标签及其内容
                            final_answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
                            
                            # 格式化为HTML，使思考过程可折叠
                            formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                            return self._format_answer(formatted_answer)
                        else:
                            # 检查是否使用了其他格式的思考过程
                            # 例如：1. 在分析这个问题时... 2. 这个问题可能... 3. 我需要确保...
                            numbered_format = re.findall(r'(\d+\.\s+[^0-9]+?)(?=\d+\.|$)', answer, re.DOTALL)
                            if numbered_format and len(numbered_format) >= 3:
                                # 提取前面的思考部分（前n-1项）
                                thinking_parts = numbered_format[:-1]
                                thinking_process = "\n\n".join([part.strip() for part in thinking_parts])
                                
                                # 最后一项可能是最终答案
                                final_answer = numbered_format[-1].strip()
                                
                                # 如果最后一项包含"最终答案"或类似字样
                                final_answer_match = re.search(r'(?:最终答案[：:]\s*|最后答案[：:]\s*)(.*?)$', final_answer, re.DOTALL)
                                if final_answer_match:
                                    final_answer = final_answer_match.group(1).strip()
                                
                                # 格式化为HTML，使思考过程可折叠
                                formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                                return self._format_answer(formatted_answer)
                            
                            # 检查是否使用了其他格式的思考过程
                            # 例如：1. **分析问题**：... 2. **思考过程**：... 3. **解决方案**：...
                            analysis_match = re.search(r'(?:1\.?\s*\*\*分析问题\*\*：|分析问题：)(.*?)(?:2\.|\*\*思考|$)', answer, re.DOTALL)
                            thinking_match = re.search(r'(?:2\.?\s*\*\*思考过程\*\*：|思考过程：)(.*?)(?:3\.|\*\*解决|$)', answer, re.DOTALL)
                            solution_match = re.search(r'(?:3\.?\s*\*\*解决方案\*\*：|解决方案：)(.*?)(?:最终答案|$)', answer, re.DOTALL)
                            
                            if analysis_match or thinking_match or solution_match:
                                # 提取思考部分
                                thinking_parts = []
                                if analysis_match:
                                    thinking_parts.append(f"**分析问题**：{analysis_match.group(1).strip()}")
                                if thinking_match:
                                    thinking_parts.append(f"**思考过程**：{thinking_match.group(1).strip()}")
                                if solution_match:
                                    thinking_parts.append(f"**解决方案**：{solution_match.group(1).strip()}")
                                
                                thinking_process = "\n\n".join(thinking_parts)
                                
                                # 提取最终答案
                                final_answer_match = re.search(r'(?:最终答案：|最终答案:|最终答案|最后答案：|最后答案:|最后答案)(.*?)$', answer, re.DOTALL)
                                if final_answer_match:
                                    final_answer = final_answer_match.group(1).strip()
                                else:
                                    # 如果没有明确的最终答案标记，尝试提取最后一段作为答案
                                    paragraphs = answer.split('\n\n')
                                    final_answer = paragraphs[-1].strip()
                                    # 如果最后一段包含分析/思考/解决方案，则使用一个通用回答
                                    if re.search(r'分析|思考|解决方案', final_answer):
                                        final_answer = "根据以上分析，我的回答是：" + re.sub(r'.*?(您好|你好).*', '您好！我是教育助手，请问有什么可以帮助您的？', answer)
                                
                                # 格式化为HTML，使思考过程可折叠
                                formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                                return self._format_answer(formatted_answer)
                    
                    return self._format_answer(answer)
                else:
                    return "Ollama服务返回了无效的响应格式"
            else:
                return f"Ollama API返回错误: {response.status_code}"
        
        except requests.exceptions.Timeout:
            return "请求Ollama服务超时，请检查服务是否正常运行"
        except requests.exceptions.ConnectionError:
            return "无法连接到Ollama服务，请确保服务正在运行"
        except Exception as e:
            logger.error(f"获取Ollama答案失败: {str(e)}")
            return f"获取答案时出错: {str(e)}"
    
    # 使用Ollama获取问题的答案（流式响应）
    def get_answer_stream_ollama(self, question: str, mode: str = 'video', context: str = None, deep_thinking: bool = False):
        import json
        import requests
        
        if mode == 'video' and not context:
            if not self.is_initialized or len(self.subtitles) == 0:
                yield "视频知识库未初始化，请先上传视频并等待处理完成"
                return
            
            # 搜索相关片段
            segments = self.search_similar_segments(question, top_k=3)
            
            if not segments:
                yield "未找到与问题相关的视频内容"
                return
            
            # 构建上下文
            context = "\n\n".join([f"片段 {i+1}（{self._format_time(seg['start_time'])} - {self._format_time(seg['end_time'])}）: {seg['text']}" 
                                for i, seg in enumerate(segments)])
        
        # 构建提示词
        prompt = f"""你是一个教育助手。请回答用户的问题。

用户问题: {question}

请提供有帮助的回答。如果你不确定答案，请诚实地说明。"""
        
        if mode == 'video':
            prompt = f"""你是一个教育视频内容助手。请根据以下视频内容片段回答用户的问题。
            
视频内容片段:
{context}

用户问题: {question}

请根据提供的视频内容片段回答问题。如果视频内容中没有足够的信息来回答问题，请说明这一点。"""
        
        logger.info(f"构建的提示词: {prompt[:100]}...")
        
        # 根据深度思考模式调整系统提示词
        system_prompt = "你是一个教育助手，请始终使用中文回答问题。"
        
        # 离线下，基于视频内容的问答模式(深度思考)
        if deep_thinking:
            system_prompt += """你必须按照以下格式回答：
1. 首先，在<think>标签内详细分析问题并展示你的思考过程
2. 然后，在标签外给出最终答案

例如：
<think>
首先，我需要理解问题的核心...
分析可能的解决方案...
考虑各种因素...
</think>

基于以上思考，我的回答是...

这个格式是强制性的，你必须将所有思考过程放在<think>标签内。
不要在回答中介绍自己，直接回答问题。"""
        else:
            system_prompt += "请直接给出简洁明了的回答，无需展示思考过程。"
        
        try:
            # 尝试先使用非流式API获取回答
            try:
                logger.info("尝试使用非流式API获取回答")
                payload_non_stream = {
                    "model": "qwen3:8b",
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False
                }
                
                non_stream_response = requests.post(
                    f"{OLLAMA_BASE_URL}/generate", 
                    json=payload_non_stream, 
                    timeout=30
                )
                
                if non_stream_response.status_code == 200:
                    response_data = non_stream_response.json()
                    if 'response' in response_data:
                        answer = response_data['response']
                        logger.info(f"非流式API成功获取回答，长度: {len(answer)}")
                        
                        # 处理深度思考模式的回答
                        if deep_thinking:
                            # 提取思考过程和最终答案
                            think_matches = re.findall(r'<think>(.*?)</think>', answer, re.DOTALL)
                            if think_matches:
                                # 合并所有思考过程
                                thinking_process = "\n\n".join([match.strip() for match in think_matches])
                                # 移除所有思考标签及其内容
                                final_answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
                                
                                # 格式化为HTML，使思考过程可折叠
                                formatted_response = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                                
                                yield self._format_answer(formatted_response)
                                return
                            else:
                                # 检查是否使用了其他格式的思考过程
                                # 例如：1. 在分析这个问题时... 2. 这个问题可能... 3. 我需要确保...
                                numbered_format = re.findall(r'(\d+\.\s+[^0-9]+?)(?=\d+\.|$)', answer, re.DOTALL)
                                if numbered_format and len(numbered_format) >= 3:
                                    # 提取前面的思考部分（前n-1项）
                                    thinking_parts = numbered_format[:-1]
                                    thinking_process = "\n\n".join([part.strip() for part in thinking_parts])
                                    
                                    # 最后一项可能是最终答案
                                    final_answer = numbered_format[-1].strip()
                                    
                                    # 如果最后一项包含"最终答案"或类似字样
                                    final_answer_match = re.search(r'(?:最终答案[：:]\s*|最后答案[：:]\s*)(.*?)$', final_answer, re.DOTALL)
                                    if final_answer_match:
                                        final_answer = final_answer_match.group(1).strip()
                                    
                                    # 格式化为HTML，使思考过程可折叠
                                    formatted_response = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                                    yield self._format_answer(formatted_response)
                                    return
                                
                                # 检查是否使用了其他格式的思考过程
                                # 例如：1. **分析问题**：... 2. **思考过程**：... 3. **解决方案**：...
                                analysis_match = re.search(r'(?:1\.?\s*\*\*分析问题\*\*：|分析问题：)(.*?)(?:2\.|\*\*思考|$)', answer, re.DOTALL)
                                thinking_match = re.search(r'(?:2\.?\s*\*\*思考过程\*\*：|思考过程：)(.*?)(?:3\.|\*\*解决|$)', answer, re.DOTALL)
                                solution_match = re.search(r'(?:3\.?\s*\*\*解决方案\*\*：|解决方案：)(.*?)(?:最终答案|$)', answer, re.DOTALL)
                                
                                if analysis_match or thinking_match or solution_match:
                                    # 提取思考部分
                                    thinking_parts = []
                                    if analysis_match:
                                        thinking_parts.append(f"**分析问题**：{analysis_match.group(1).strip()}")
                                    if thinking_match:
                                        thinking_parts.append(f"**思考过程**：{thinking_match.group(1).strip()}")
                                    if solution_match:
                                        thinking_parts.append(f"**解决方案**：{solution_match.group(1).strip()}")
                                    
                                    thinking_process = "\n\n".join(thinking_parts)
                                    
                                    # 提取最终答案
                                    final_answer_match = re.search(r'(?:最终答案：|最终答案:|最终答案|最后答案：|最后答案:|最后答案)(.*?)$', answer, re.DOTALL)
                                    if final_answer_match:
                                        final_answer = final_answer_match.group(1).strip()
                                    else:
                                        # 如果没有明确的最终答案标记，尝试提取最后一段作为答案
                                        paragraphs = answer.split('\n\n')
                                        final_answer = paragraphs[-1].strip()
                                        # 如果最后一段包含分析/思考/解决方案，则使用一个通用回答
                                        if re.search(r'分析|思考|解决方案', final_answer):
                                            final_answer = "根据以上分析，我的回答是：" + re.sub(r'.*?(您好|你好).*', '您好！我是教育助手，请问有什么可以帮助您的？', answer)
                                    
                                    # 格式化为HTML，使思考过程可折叠
                                    formatted_response = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                                    yield self._format_answer(formatted_response)
                                    return
                        
                        yield self._format_answer(answer)
                        return
                    else:
                        logger.warning("非流式API返回成功但没有response字段")
                else:
                    logger.warning(f"非流式API请求失败: {non_stream_response.status_code}")
            except Exception as e:
                logger.warning(f"非流式API请求出错: {str(e)}，将尝试流式API")
            
            # 如果非流式API失败，尝试流式API
            logger.info("尝试使用流式API获取回答")
            payload = {
                "model": "qwen3:8b",
                "prompt": prompt,
                "system": system_prompt,
                "stream": True
            }
            
            logger.info(f"发送请求到Ollama API: {OLLAMA_BASE_URL}/generate，使用模型: qwen3:8b")
            
            # 如果没有收到响应，提供一个默认回答
            has_yielded = False
            start_time = time.time()
            timeout_seconds = 15  # 设置15秒超时
            
            try:
                with requests.post(f"{OLLAMA_BASE_URL}/generate", json=payload, stream=True, timeout=timeout_seconds) as response:
                    logger.info(f"Ollama API响应状态码: {response.status_code}")
                    
                    if response.status_code != 200:
                        logger.error(f"Ollama API返回错误: {response.status_code}, 响应内容: {response.text}")
                        yield f"Ollama API返回错误: {response.status_code}。请检查Ollama服务是否正常运行，或尝试使用在线模式。"
                        return
                    
                    logger.info(f"Ollama API返回成功，开始处理流式响应")
                    
                    # 创建一个缓冲区来收集完整的响应
                    complete_response = ""
                    
                    # 逐行读取流式响应
                    line_count = 0
                    for line in response.iter_lines():
                        line_count += 1
                        logger.info(f"处理响应行 #{line_count}")
                        
                        if line:
                            try:
                                # 解析JSON响应
                                line_text = line.decode('utf-8')
                                logger.info(f"收到原始响应行: {line_text[:100]}...")
                                
                                try:
                                    data = json.loads(line_text)
                                    current_chunk = ""
                                    
                                    if 'response' in data:
                                        current_chunk = data['response']
                                        logger.info(f"收到Ollama响应片段: {current_chunk[:20]}...")
                                        has_yielded = True
                                        
                                        # 将当前块添加到完整响应中
                                        complete_response += current_chunk
                                        
                                        # 如果是深度思考模式，我们需要收集完整的响应后再处理
                                        if deep_thinking and "<think>" in complete_response and "</think>" in complete_response:
                                            # 检查是否有完整的思考标签对
                                            think_open_count = complete_response.count("<think>")
                                            think_close_count = complete_response.count("</think>")
                                            
                                            # 如果有完整的思考标签对
                                            if think_open_count > 0 and think_open_count == think_close_count:
                                                # 提取思考过程
                                                think_matches = re.findall(r'<think>(.*?)</think>', complete_response, re.DOTALL)
                                                if think_matches:
                                                    # 合并所有思考过程
                                                    thinking_process = "\n\n".join([match.strip() for match in think_matches])
                                                    # 移除所有思考标签及其内容
                                                    final_answer = re.sub(r'<think>.*?</think>', '', complete_response, flags=re.DOTALL).strip()
                                                    
                                                    # 格式化为HTML，使思考过程可折叠
                                                    formatted_response = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                                                    yield self._format_answer(formatted_response)
                                                    return
                                        
                                        # 如果不是深度思考模式或没有完整的思考标签对，直接输出当前块
                                        yield self._format_answer(current_chunk)
                                    elif 'error' in data:
                                        logger.error(f"Ollama返回错误: {data['error']}")
                                        has_yielded = True
                                        yield f"Ollama错误: {data['error']}。请检查Ollama服务是否正常运行，或尝试使用在线模式。"
                                except json.JSONDecodeError as e:
                                    logger.error(f"无法解析JSON: {line_text}, 错误: {str(e)}")
                                    continue
                            except Exception as e:
                                logger.error(f"处理响应行出错: {str(e)}")
                                continue
                            
                            # 检查是否超时
                            if time.time() - start_time > timeout_seconds * 2:  # 给予两倍的超时时间
                                logger.error("Ollama响应处理超时")
                                if not has_yielded:
                                    yield "处理请求超时，请检查Ollama服务是否正常运行，或尝试使用在线模式。"
                                return
                
                logger.info("Ollama流式响应结束")
            except requests.exceptions.Timeout:
                logger.error(f"Ollama API请求超时（{timeout_seconds}秒）")
                yield f"Ollama API请求超时（{timeout_seconds}秒）。请检查Ollama服务是否正常运行，或尝试使用在线模式。"
                return
            except requests.exceptions.ConnectionError:
                logger.error("无法连接到Ollama服务")
                yield "无法连接到Ollama服务。请确保Ollama服务正在运行，或尝试使用在线模式。"
                return
                
            # 如果没有收到任何响应，返回一个默认回答
            if not has_yielded:
                logger.warning("未收到Ollama任何响应，返回默认回答")
                yield "我是AI助手，很抱歉，我目前无法处理您的请求。这可能是因为Ollama模型对中文支持有限或服务不稳定。请尝试使用在线模式或联系管理员。"
                
            # 处理深度思考模式的回答
            if deep_thinking and has_yielded:
                # 提取思考过程和最终答案
                think_matches = re.findall(r'<think>(.*?)</think>', complete_response, re.DOTALL)
                if think_matches:
                    # 合并所有思考过程，如果thinking_process已经有内容，则添加到现有内容中
                    if thinking_process:
                        thinking_process += "\n\n" + "\n\n".join([match.strip() for match in think_matches])
                    else:
                        thinking_process = "\n\n".join([match.strip() for match in think_matches])
                    # 移除所有思考标签及其内容
                    final_answer = re.sub(r'<think>.*?</think>', '', complete_response, flags=re.DOTALL).strip()
                    
                    # 格式化为HTML，使思考过程可折叠
                    formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                    yield self._format_answer(formatted_answer)
                else:
                    # 检查是否使用了其他格式的思考过程
                    # 例如：1. 在分析这个问题时... 2. 这个问题可能... 3. 我需要确保...
                    numbered_format = re.findall(r'(\d+\.\s+[^0-9]+?)(?=\d+\.|$)', complete_response, re.DOTALL)
                    if numbered_format and len(numbered_format) >= 3:
                        # 提取前面的思考部分（前n-1项）
                        thinking_parts = numbered_format[:-1]
                        new_thinking = "\n\n".join([part.strip() for part in thinking_parts])
                        
                        # 累积思考过程，而不是替换
                        if thinking_process:
                            thinking_process += "\n\n" + new_thinking
                        else:
                            thinking_process = new_thinking
                        
                        # 最后一项可能是最终答案
                        final_answer = numbered_format[-1].strip()
                        
                        # 如果最后一项包含"最终答案"或类似字样
                        final_answer_match = re.search(r'(?:最终答案[：:]\s*|最后答案[：:]\s*)(.*?)$', final_answer, re.DOTALL)
                        if final_answer_match:
                            final_answer = final_answer_match.group(1).strip()
                        
                        # 格式化为HTML，使思考过程可折叠
                        formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                        yield self._format_answer(formatted_answer)
                    
                    # 检查是否使用了其他格式的思考过程
                    # 例如：1. **分析问题**：... 2. **思考过程**：... 3. **解决方案**：...
                    analysis_match = re.search(r'(?:1\.?\s*\*\*分析问题\*\*：|分析问题：)(.*?)(?:2\.|\*\*思考|$)', complete_response, re.DOTALL)
                    thinking_match = re.search(r'(?:2\.?\s*\*\*思考过程\*\*：|思考过程：)(.*?)(?:3\.|\*\*解决|$)', complete_response, re.DOTALL)
                    solution_match = re.search(r'(?:3\.?\s*\*\*解决方案\*\*：|解决方案：)(.*?)(?:最终答案|$)', complete_response, re.DOTALL)
                    
                    if analysis_match or thinking_match or solution_match:
                        # 提取思考部分
                        thinking_parts = []
                        if analysis_match:
                            thinking_parts.append(f"**分析问题**：{analysis_match.group(1).strip()}")
                        if thinking_match:
                            thinking_parts.append(f"**思考过程**：{thinking_match.group(1).strip()}")
                        if solution_match:
                            thinking_parts.append(f"**解决方案**：{solution_match.group(1).strip()}")
                        
                        new_thinking = "\n\n".join(thinking_parts)
                        
                        # 累积思考过程，而不是替换
                        if thinking_process:
                            thinking_process += "\n\n" + new_thinking
                        else:
                            thinking_process = new_thinking
                        
                        # 提取最终答案
                        final_answer_match = re.search(r'(?:最终答案：|最终答案:|最终答案|最后答案：|最后答案:|最后答案)(.*?)$', complete_response, re.DOTALL)
                        if final_answer_match:
                            final_answer = final_answer_match.group(1).strip()
                        else:
                            # 如果没有明确的最终答案标记，尝试提取最后一段作为答案
                            paragraphs = complete_response.split('\n\n')
                            final_answer = paragraphs[-1].strip()
                            # 如果最后一段包含分析/思考/解决方案，则使用一个通用回答
                            if re.search(r'分析|思考|解决方案', final_answer):
                                final_answer = "根据以上分析，我的回答是：" + re.sub(r'.*?(您好|你好).*', '您好！我是教育助手，请问有什么可以帮助您的？', complete_response)
                        
                        # 格式化为HTML，使思考过程可折叠
                        formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                        yield self._format_answer(formatted_answer)
                    
                    # 如果没有找到思考标签，可能是模型没有按照指令生成思考过程
                    # 在这种情况下，我们生成一个通用的思考过程
                    logger.warning("深度思考模式下未找到标准思考格式，生成通用思考过程")
                    
                    # 提取问题
                    question_text = ""
                    try:
                        question_text = prompt.split('用户问题: ')[1].split('\n')[0]
                    except:
                        question_text = "未能提取到具体问题"
                    
                    thinking_process = f"""**分析问题**："{question_text}"

首先，我需要仔细理解用户提出的问题，确定问题的核心要点和用户的真实需求。这个问题可能涉及到视频内容分析、概念解释、知识点梳理或其他教育相关主题。

**思考过程**：
1. 我需要回顾视频中提到的关键信息和核心概念
2. 分析这些概念之间的逻辑关系和层次结构
3. 考虑不同角度的解释和可能的应用场景
4. 整合相关的背景知识和上下文信息
5. 确保回答的准确性、全面性和教育价值

**解决方案**：
基于以上分析，我将提供一个结构清晰、内容准确的回答，帮助用户深入理解相关知识点。我会关注回答的教育意义，确保信息的可靠性，并尽可能提供有价值的延伸思考。"""
                    
                    formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{complete_response}"""
                    yield self._format_answer(formatted_answer)
            
        except Exception as e:
            logger.error(f"Ollama流式响应出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            yield f"Ollama服务出错: {str(e)}。请检查Ollama服务是否正常运行，或尝试使用在线模式。"
    
    def _format_time(self, seconds):
        """将秒数格式化为时:分:秒格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    # 格式化回答文本，使其更加美观
    def _format_answer(self, answer):
        """
        格式化回答文本，使其更加美观
        
        Args:
            answer: 原始回答文本
            
        Returns:
            str: 格式化后的回答文本
        """
        if not answer:
            return answer
            
        # 处理已经包含HTML标签的内容（如深度思考模式的折叠内容）
        if "<details>" in answer:
            # 确保details标签内容格式正确
            answer = re.sub(r'<details>\s*<summary>(.*?)</summary>\s*<p>(.*?)</p>\s*</details>', 
                           r'<details class="thinking-details">\n<summary>\1</summary>\n<div class="thinking-content">\2</div>\n</details>', 
                           answer, flags=re.DOTALL)
        
        # 处理普通文本格式
        # 1. 处理编号列表（如：1. 内容 2. 内容）
        if re.search(r'^\d+\.\s', answer, re.MULTILINE):
            # 将编号列表转换为HTML有序列表
            processed_lines = []
            current_list = []
            in_list = False
            
            for line in answer.split('\n'):
                list_match = re.match(r'(\d+)\.\s+(.*)', line)
                if list_match:
                    if not in_list:
                        in_list = True
                        if current_list:  # 如果有之前收集的非列表内容
                            processed_lines.append('<p class="answer-paragraph">' + ' '.join(current_list) + '</p>')
                            current_list = []
                        processed_lines.append('<ol class="answer-list">')
                    
                    # 处理列表项内的加粗文本
                    item_content = list_match.group(2)
                    item_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', item_content)
                    
                    processed_lines.append(f'<li>{item_content}</li>')
                else:
                    if in_list and line.strip():  # 非空行但不是列表项
                        in_list = False
                        processed_lines.append('</ol>')
                    
                    if line.strip():  # 非空行
                        # 处理独立的加粗文本
                        line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
                        current_list.append(line)
                    elif current_list:  # 空行且有收集的内容
                        processed_lines.append('<p class="answer-paragraph">' + ' '.join(current_list) + '</p>')
                        current_list = []
            
            # 处理最后的内容
            if in_list:
                processed_lines.append('</ol>')
            elif current_list:
                processed_lines.append('<p class="answer-paragraph">' + ' '.join(current_list) + '</p>')
            
            answer = ''.join(processed_lines)
        else:
            # 2. 处理普通段落和加粗文本
            paragraphs = answer.split('\n\n')
            formatted_paragraphs = []
            
            for para in paragraphs:
                if para.strip():
                    # 处理加粗文本
                    para = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', para)
                    
                    # 检查是否为标题（以#开头）
                    if re.match(r'^#+\s', para):
                        heading_level = len(re.match(r'^(#+)\s', para).group(1))
                        heading_text = re.sub(r'^#+\s', '', para)
                        para = f'<h{heading_level} class="answer-heading">{heading_text}</h{heading_level}>'
                    else:
                        # 将段落中的换行符替换为空格，减少行间距
                        para = para.replace('\n', ' ')
                        para = f'<p class="answer-paragraph">{para}</p>'
                    
                    formatted_paragraphs.append(para)
            
            answer = ''.join(formatted_paragraphs)
        
        # 添加整体的样式类
        answer = f'<div class="formatted-answer">{answer}</div>'
        
        return answer