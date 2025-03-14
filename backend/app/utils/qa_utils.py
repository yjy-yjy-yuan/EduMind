import os
try:
    import faiss
    FAISS_AVAILABLE = True
    print("成功初始化GPU资源")
except ImportError:
    FAISS_AVAILABLE = False
    import logging
    logging.warning("警告: 未找到faiss模块，QA功能将受限")
    print("警告: 未找到faiss模块，QA功能将受限")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    import logging
    logging.warning("警告: 未找到sentence_transformers模块，QA功能将受限")
    print("警告: 未找到sentence_transformers模块，QA功能将受限")

import numpy as np
import re
from typing import List, Dict, Tuple
from openai import OpenAI

class QASystem:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        # 初始化向量模型
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence_transformers模块不可用")
        self.model = SentenceTransformer(model_name)
        # 初始化 FAISS 资源
        self.use_gpu = False
        
        # 如果FAISS可用，尝试使用GPU
        if FAISS_AVAILABLE:
            try:
                # 检查是否有GPU资源
                res = faiss.StandardGpuResources()
                self.use_gpu = True
                self.res = res
                print("FAISS GPU资源初始化成功")
            except Exception as e:
                print(f"FAISS GPU初始化失败: {e}")
                self.use_gpu = False
        else:
            print("FAISS模块不可用，将使用备用方式")
            
        # 存储向量
        self.vectors = None
        # 初始化FAISS索引
        self.index = None
        # 存储文本
        self.texts = []
        # 存储时间戳信息
        self.timestamps = []
        
    def _create_index(self, dimension):
        """创建 FAISS 索引"""
        if not FAISS_AVAILABLE:
            print("FAISS模块不可用，无法创建索引")
            return None
            
        try:
            # 先清理之前的索引
            if self.index is not None:
                del self.index
                self.index = None
            
            # 创建 CPU 索引
            cpu_index = faiss.IndexFlatL2(dimension)
            
            if self.use_gpu:
                try:
                    # 尝试创建 GPU 索引
                    gpu_index = faiss.index_cpu_to_gpu(self.res, 0, cpu_index)
                    print("成功创建GPU索引")
                    return gpu_index
                except Exception as e:
                    print(f"GPU 索引创建失败，回退到 CPU 索引: {str(e)}")
                    return cpu_index
            else:
                return cpu_index
                
        except Exception as e:
            print(f"索引创建失败: {str(e)}")
            return None
            
    def _parse_timestamp(self, timestamp_str: str) -> Tuple[str, str]:
        """解析时间戳字符串，返回开始和结束时间"""
        match = re.match(r'\[(.*?)\s*-->\s*(.*?)\]', timestamp_str)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return None, None
        
    def create_knowledge_base(self, subtitle_path):
        """从字幕文件创建知识库"""
        if not os.path.exists(subtitle_path):
            raise FileNotFoundError(f"字幕文件不存在: {subtitle_path}")
            
        # 读取字幕文件
        try:
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if not content.strip():
                raise ValueError("字幕文件内容为空")
                
            # 将内容分割成段落
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            if not paragraphs:
                raise ValueError("字幕文件格式无效，无法分割段落")
                
            # 提取文本内容和时间戳
            texts = []
            timestamps = []
            
            print(f"开始处理字幕文件，共有 {len(paragraphs)} 个段落")
            
            for i, p in enumerate(paragraphs):
                try:
                    timestamp_end = p.find(']')
                    if timestamp_end == -1:
                        # 尝试其他格式的字幕
                        lines = p.split('\n')
                        if len(lines) >= 3:
                            # 可能是SRT格式
                            time_line = lines[1]
                            time_match = re.search(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', time_line)
                            if time_match:
                                start_time = time_match.group(1)
                                end_time = time_match.group(2)
                                text = '\n'.join(lines[2:]).strip()
                                texts.append(text)
                                timestamps.append({
                                    "start_time": start_time,
                                    "end_time": end_time
                                })
                                continue
                        print(f"段落 {i+1} 没有找到时间戳: {p[:50]}...")
                        continue
                    
                    timestamp_str = p[:timestamp_end+1]
                    text = p[timestamp_end+1:].strip()
                    
                    if not text:
                        print(f"段落 {i+1} 文本内容为空: {timestamp_str}")
                        continue
                    
                    start_time, end_time = self._parse_timestamp(timestamp_str)
                    if start_time and end_time:
                        texts.append(text)
                        timestamps.append({
                            "start_time": start_time,
                            "end_time": end_time
                        })
                    else:
                        print(f"段落 {i+1} 时间戳解析失败: {timestamp_str}")
                except Exception as e:
                    print(f"处理段落 {i+1} 时出错: {str(e)}")
                    continue
                    
            if not texts:
                raise ValueError("未找到有效的字幕内容，请检查字幕文件格式")
                
            print(f"成功提取了 {len(texts)} 段有效字幕内容")
                
            # 将文本转换为向量
            vectors = self.model.encode(texts)
            vectors = vectors.astype('float32')
            
            # 创建索引
            dimension = vectors.shape[1]
            self.index = self._create_index(dimension)
            if self.index is None and FAISS_AVAILABLE:
                print("无法创建索引")
                raise RuntimeError("无法创建索引")
                
            # 添加向量到索引
            if FAISS_AVAILABLE and self.index:
                self.index.add(vectors)
            
            # 保存文本和时间戳
            self.texts = texts
            self.timestamps = timestamps
            
            print(f"知识库创建成功，包含 {len(texts)} 个文本片段")
            
            return self.index
            
        except Exception as e:
            print(f"创建知识库时出错: {str(e)}")
            # 清空状态
            self.texts = []
            self.timestamps = []
            self.index = None
            raise
            
    def search_similar_segments(self, query: str, top_k: int = 3) -> List[Dict]:
        """搜索与查询最相似的片段"""
        if not self.texts:
            raise ValueError("知识库未初始化")
            
        # 将查询转换为向量
        query_vector = self.model.encode([query])
        query_vector = query_vector.astype('float32')
        
        # 搜索最相似的片段
        results = []
        
        if FAISS_AVAILABLE and self.index:
            # 使用FAISS搜索
            distances, indices = self.index.search(query_vector, top_k)
            
            for i, idx in enumerate(indices[0]):
                if idx < len(self.texts):
                    results.append({
                        'text': self.texts[idx],
                        'timestamp': self.timestamps[idx],
                        'score': float(distances[0][i])
                    })
        else:
            # 备用方案：返回前几个文档
            for i, text in enumerate(self.texts[:top_k]):
                results.append({
                    'text': text,
                    'timestamp': self.timestamps[i],
                    'score': 0.0  # 无法计算相似度分数
                })
                
        return results
        
    def get_answer(self, question: str, api_key: str, mode: str = 'video', context: str = None) -> str:
        """获取问题的答案（非流式）"""
        if not api_key:
            raise ValueError("需要提供OpenAI API密钥")
            
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        if mode == 'video':
            if not self.index or not self.texts:
                raise ValueError("知识库未初始化，无法回答基于视频的问题")
                
            # 搜索相关片段
            similar_segments = self.search_similar_segments(question, top_k=3)
            context = "\n".join([seg['text'] for seg in similar_segments])
            
            # 构建提示
            prompt = f"""基于以下视频内容回答问题。如果问题无法从内容中得到答案，请说明无法回答。

内容：
{context}

问题：{question}"""
            
        else:  # 自由对话模式
            prompt = f"""你是一个教育助手。请回答以下问题，提供安全、有帮助、准确的回答：

问题：{question}"""
            
        try:
            # 创建聊天完成
            response = client.chat.completions.create(
                model="qwen-turbo",
                messages=[
                    {"role": "system", "content": "你是一个教育助手。你会为用户提供安全，有帮助，准确的回答。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"获取答案时出错: {str(e)}")
            
    def get_answer_stream(self, question: str, api_key: str, mode: str = 'video', context: str = None):
        """获取问题的答案（流式响应）"""
        if not api_key:
            raise ValueError("需要提供OpenAI API密钥")
            
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        if mode == 'video':
            if not self.index or not self.texts:
                raise ValueError("知识库未初始化，无法回答基于视频的问题")
                
            # 搜索相关片段
            similar_segments = self.search_similar_segments(question, top_k=3)
            context = "\n".join([seg['text'] for seg in similar_segments])
            
            # 构建提示
            prompt = f"""基于以下视频内容回答问题。如果问题无法从内容中得到答案，请说明无法回答。

内容：
{context}

问题：{question}"""
            
        else:  # 自由对话模式
            prompt = f"""你是一个教育助手。请回答以下问题，提供安全、有帮助、准确的回答：

问题：{question}"""
            
        try:
            # 创建流式聊天完成
            stream = client.chat.completions.create(
                model="qwen-turbo",
                messages=[
                    {"role": "system", "content": "你是一个教育助手。你会为用户提供安全，有帮助，准确的回答。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                stream=True  # 启用流式输出
            )
            
            # 用于收集完整的回答
            full_response = ""
            
            # 逐个词语返回回答
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            return full_response
            
        except Exception as e:
            error_msg = f"获取答案时出错: {str(e)}"
            yield error_msg
            return error_msg
