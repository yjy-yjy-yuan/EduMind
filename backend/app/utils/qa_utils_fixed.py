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

def check_ollama_service():
    """检查Ollama服务是否可用"""
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

# 检查Ollama服务是否可用
check_ollama_service()

class QASystem:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """
        初始化问答系统
        
        Args:
            model_name: 使用的Sentence Transformer模型名称
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
    
    def _create_index(self, dimension):
        """
        创建 FAISS 索引
        
        Args:
            dimension: 向量维度
        
        Returns:
            FAISS 索引对象
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
    
    def _parse_timestamp(self, timestamp_str: str) -> Tuple[float, float]:
        """解析时间戳字符串，返回开始和结束时间"""
        parts = timestamp_str.split(' --> ')
        start_time = self._time_to_seconds(parts[0])
        end_time = self._time_to_seconds(parts[1])
        return start_time, end_time
    
    def create_knowledge_base(self, subtitle_path):
        """
        从字幕文件创建知识库
        
        Args:
            subtitle_path: 字幕文件路径
        
        Returns:
            bool: 是否成功创建知识库
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
    
    def _time_to_seconds(self, time_str):
        """将时间字符串转换为秒数"""
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    
    def search_similar_segments(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        搜索与查询最相似的片段
        
        Args:
            query: 查询文本
            top_k: 返回的结果数量
        
        Returns:
            List[Dict]: 相似片段列表
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
    
    def get_answer(self, question: str, api_key: str = None, mode: str = 'video', use_ollama: bool = False, deep_thinking: bool = False):
        """
        获取问题的答案
        
        Args:
            question: 用户问题
            api_key: OpenAI API密钥
            mode: 问答模式，'video'或'free'
            use_ollama: 是否使用Ollama本地模型
            deep_thinking: 是否启用深度思考模式
        
        Returns:
            str: 问题的答案
        """
        if use_ollama:
            return self.get_answer_ollama(question, mode, deep_thinking=deep_thinking)
        
        if not api_key:
            return "请提供有效的API密钥"
        
        try:
            import openai
            openai.api_key = api_key
            
            if mode == 'video':
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
                prompt = f"""你是一个教育视频内容助手。请根据以下视频内容片段回答用户的问题。
                
视频内容片段:
{context}

用户问题: {question}

请根据提供的视频内容片段回答问题。如果视频内容中没有足够的信息来回答问题，请说明这一点。"""
            else:
                # 自由问答模式
                prompt = f"""你是一个教育助手。请回答用户的问题。

用户问题: {question}

请提供有帮助的回答。如果你不确定答案，请诚实地说明。"""
            
            # 调用OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个教育助手，请始终使用中文回答问题。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content.strip()
            return answer
        
        except Exception as e:
            logger.error(f"获取答案失败: {str(e)}")
            return f"获取答案时出错: {str(e)}"
    
    def _format_time(self, seconds):
        """将秒数格式化为时:分:秒格式"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    
    def get_answer_ollama(self, question: str, mode: str = 'video', context: str = None, deep_thinking: bool = False):
        """
        使用Ollama获取问题的答案（非流式）
        
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
            if mode == 'video':
                prompt = f"""你是一个教育视频内容助手。请根据以下视频内容片段回答用户的问题。
                
视频内容片段:
{context}

用户问题: {question}

请根据提供的视频内容片段回答问题。如果视频内容中没有足够的信息来回答问题，请说明这一点。"""
            else:
                # 自由问答模式
                prompt = f"""你是一个教育助手。请回答用户的问题。

用户问题: {question}

请提供有帮助的回答。如果你不确定答案，请诚实地说明。"""
            
            # 根据深度思考模式调整系统提示词
            system_prompt = "你是一个教育助手。请始终使用中文回答问题。"
            if deep_thinking:
                system_prompt += "请先详细思考问题，将思考过程放在<think>标签内，然后给出简洁明了的回答。例如：<think>这里是详细的思考过程...</think>\n\n这里是最终回答。"
            else:
                system_prompt += "请直接给出简洁明了的回答，无需展示思考过程。"
            
            # 使用哪个模型
            model_to_use = "llama3"  # 默认使用llama3
            
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
                timeout=30  # 设置30秒超时
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if 'response' in response_data:
                    answer = response_data['response']
                    
                    # 处理深度思考模式的回答
                    if deep_thinking:
                        # 提取思考过程和最终答案
                        think_match = re.search(r'<think>(.*?)</think>', answer, re.DOTALL)
                        if think_match:
                            thinking_process = think_match.group(1).strip()
                            final_answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
                            
                            # 格式化为HTML，使思考过程可折叠
                            formatted_answer = f"""<details>
<summary>思考过程（点击展开）</summary>
<p>{thinking_process}</p>
</details>

{final_answer}"""
                            return formatted_answer
                    
                    return answer
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
    
    def get_answer_stream(self, question: str, api_key: str, mode: str = 'video', context: str = None, use_ollama: bool = False):
        """
        获取问题的答案（流式响应）
        
        Args:
            question: 用户问题
            api_key: OpenAI API密钥
            mode: 问答模式，'video'或'free'
            context: 可选的上下文信息
            use_ollama: 是否使用Ollama本地模型
        
        Yields:
            str: 答案的片段
        """
        if use_ollama:
            yield from self.get_answer_stream_ollama(question, mode, context)
            return
        
        if not api_key:
            yield "请提供有效的API密钥"
            return
        
        try:
            import openai
            openai.api_key = api_key
            
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
            if mode == 'video':
                prompt = f"""你是一个教育视频内容助手。请根据以下视频内容片段回答用户的问题。
                
视频内容片段:
{context}

用户问题: {question}

请根据提供的视频内容片段回答问题。如果视频内容中没有足够的信息来回答问题，请说明这一点。"""
            else:
                # 自由问答模式
                prompt = f"""你是一个教育助手。请回答用户的问题。

用户问题: {question}

请提供有帮助的回答。如果你不确定答案，请诚实地说明。"""
            
            # 调用OpenAI API（流式）
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个教育助手，请始终使用中文回答问题。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                stream=True
            )
            
            for chunk in response:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    if 'delta' in chunk['choices'][0] and 'content' in chunk['choices'][0]['delta']:
                        content = chunk['choices'][0]['delta']['content']
                        yield content
        
        except Exception as e:
            logger.error(f"流式获取答案失败: {str(e)}")
            yield f"获取答案时出错: {str(e)}"
            
    def get_answer_stream_ollama(self, question: str, mode: str = 'video', context: str = None):
        """使用Ollama获取问题的答案（流式响应）"""
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
        if mode == 'video':
            prompt = f"""你是一个教育视频内容助手。请根据以下视频内容片段回答用户的问题。
            
视频内容片段:
{context}

用户问题: {question}"""
        else:
            # 自由问答模式
            prompt = f"""你是一个教育助手。请回答用户的问题。

用户问题: {question}"""
            
        logger.info(f"构建的提示词: {prompt[:100]}...")
        
        # 根据深度思考模式调整系统提示词
        system_prompt = "你是一个教育助手。请始终使用中文回答问题。"
        if deep_thinking:
            system_prompt += "请先详细思考问题，将思考过程放在<think>标签内，然后给出简洁明了的回答。例如：<think>这里是详细的思考过程...</think>\n\n这里是最终回答。"
        else:
            system_prompt += "请直接给出简洁明了的回答，无需展示思考过程。"
        
        # 使用哪个模型
        model_to_use = "llama3"  # 默认使用llama3
        
        try:
            # 尝试先使用非流式API获取回答
            try:
                logger.info("尝试使用非流式API获取回答")
                payload_non_stream = {
                    "model": model_to_use,
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
                        yield answer
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
                "model": model_to_use,
                "prompt": prompt,
                "system": system_prompt,
                "stream": True
            }
            
            logger.info(f"发送请求到Ollama API: {OLLAMA_BASE_URL}/generate，使用模型: {model_to_use}")
            
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
                                data = json.loads(line_text)
                                
                                if 'response' in data:
                                    chunk = data['response']
                                    logger.info(f"收到Ollama响应片段: {chunk[:20]}...")
                                    has_yielded = True
                                    yield chunk
                                elif 'error' in data:
                                    logger.error(f"Ollama返回错误: {data['error']}")
                                    has_yielded = True
                                    yield f"Ollama错误: {data['error']}。请检查Ollama服务是否正常运行，或尝试使用在线模式。"
                            except json.JSONDecodeError as e:
                                logger.error(f"无法解析JSON: {line}, 错误: {str(e)}")
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
                
        except Exception as e:
            logger.error(f"Ollama流式响应出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            yield f"Ollama服务出错: {str(e)}。请检查Ollama服务是否正常运行，或尝试使用在线模式。"
