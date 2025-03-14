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
            
            # 创建 CPU 索引 - 使用内积索引用于余弦相似度（向量需要归一化）
            # 注意：使用IndexFlatIP时，相似度越高，分数越大（正值）
            cpu_index = faiss.IndexFlatIP(dimension)
            
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
            
            # L2归一化，用于余弦相似度
            vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
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
            
    def search_similar_segments(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索与查询最相似的片段"""
        if not self.texts:
            raise ValueError("知识库未初始化")
            
        # 将查询转换为向量
        query_vector = self.model.encode([query])
        
        # L2归一化，用于余弦相似度
        query_vector = query_vector / np.linalg.norm(query_vector, axis=1, keepdims=True)
        query_vector = query_vector.astype('float32')
        
        # 搜索最相似的片段
        results = []
        
        if FAISS_AVAILABLE and self.index:
            # 使用FAISS搜索
            # 增加检索数量，提高覆盖率
            # 这里的search_k是初始检索的数量，越大越能找到更多潜在相关的片段
            search_k = min(20, len(self.texts))  # 搜索更多结果，最多20个或全部文本
            similarities, indices = self.index.search(query_vector, search_k)
            
            print(f"搜索查询: '{query}'")
            print(f"初始检索数量: {search_k}")
            print(f"检索到 {len(indices[0])} 个结果")
            print(f"相似度分数: {similarities[0]}")
            
            # 注意：使用IndexFlatIP时，相似度越高，分数越大（正值）
            # 对于余弦相似度，范围是[-1, 1]，但由于向量归一化，实际上是[0, 1]
            # 设置较低的阈值以确保能找到足够的结果
            min_similarity_threshold = 0.5  # 降低相似度阈值
            
            # 过滤的意义：移除相似度过低的结果，确保只返回真正相关的内容
            filtered_results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.texts) and similarities[0][i] >= min_similarity_threshold:
                    filtered_results.append({
                        'text': self.texts[idx],
                        'timestamp': self.timestamps[idx],
                        'score': float(similarities[0][i])
                    })
                    print(f"接受的结果 #{i}: 分数={similarities[0][i]}, 文本={self.texts[idx][:50]}...")
                else:
                    if idx < len(self.texts):
                        print(f"拒绝的结果 #{i}: 分数={similarities[0][i]}, 文本={self.texts[idx][:50]}...")
            
            print(f"过滤后结果数量: {len(filtered_results)}")
            
            # 如果过滤后的结果太少，放宽限制
            if len(filtered_results) < 2:
                print("过滤后结果太少，放宽限制...")
                # 完全放宽限制，直接返回前top_k个结果
                results = [{
                    'text': self.texts[idx],
                    'timestamp': self.timestamps[idx],
                    'score': float(similarities[0][i])
                } for i, idx in enumerate(indices[0][:top_k]) if idx < len(self.texts)]
                print(f"放宽限制后结果数量: {len(results)}")
            else:
                # 返回所有过滤后的结果，不限制数量
                results = filtered_results
                print(f"最终返回结果数量: {len(results)}")
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
            similar_segments = self.search_similar_segments(question, top_k=5)
            
            # 检查是否找到相关内容
            if len(similar_segments) == 0:
                print(f"未找到与问题 '{question}' 相关的内容")
                prompt = f"""你是一个教育助手。用户问了以下问题，但我未能在视频内容中找到相关信息。请礼貌地告知用户：

问题：{question}

请告知用户视频内容中没有相关信息，并建议用户尝试其他问题或使用自由问答模式。"""
            else:
                # 格式化上下文，包含时间戳
                context = "\n".join([f"[{seg['timestamp']['start_time']} --> {seg['timestamp']['end_time']}] {seg['text']}" for seg in similar_segments])
                print(f"找到相关内容: {context}")
                
                # 构建更强的提示词模板
                prompt = f"""你是一个教育视频内容助手。请基于以下视频内容片段回答用户问题。这些片段可能很短，但它们包含了重要信息。

视频内容片段：
{context}

用户问题：{question}

指导原则：
1. 即使视频内容片段很短或看似不完整，也请尽量从中提取有用信息来回答问题
2. 视频内容片段中的任何文字都可能是有用的线索，请充分利用
3. 如果视频内容片段确实无法回答问题，再说明"视频内容中没有提供相关信息"
4. 绝对不要编造不在视频内容中的信息
5. 回答要简洁、准确、有条理
6. 如果合适，可以引用视频中的具体时间点"""
            
        else:  # 自由对话模式
            prompt = f"""你是一个教育助手。请回答以下问题，提供安全、有帮助、准确的回答：

问题：{question}"""
            
        try:
            # 创建聊天完成
            response = client.chat.completions.create(
                model="qwen-turbo",
                messages=[
                    {"role": "system", "content": "你是一个教育助手。你会为用户提供安全，有帮助，准确的回答。即使只有很短的信息片段，也要尽量从中提取有用信息来回答问题。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7  # 增加温度参数，提高创造性
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
            similar_segments = self.search_similar_segments(question, top_k=5)
            
            # 检查是否找到相关内容 - 不应该为空，因为我们已经放宽了限制
            # 只有在similar_segments为空列表时才认为没有找到相关内容
            if len(similar_segments) == 0:
                print(f"未找到与问题 '{question}' 相关的内容")
                prompt = f"""你是一个教育助手。用户问了以下问题，但我未能在视频内容中找到相关信息。请礼貌地告知用户：

问题：{question}

请告知用户视频内容中没有相关信息，并建议用户尝试其他问题或使用自由问答模式。"""
            else:
                # 格式化上下文，包含时间戳
                context = "\n".join([f"[{seg['timestamp']['start_time']} --> {seg['timestamp']['end_time']}] {seg['text']}" for seg in similar_segments])
                print(f"找到相关内容: {context}")
                
                # 构建更强的提示词模板
                prompt = f"""你是一个教育视频内容助手。请基于以下视频内容片段回答用户问题。这些片段可能很短，但它们包含了重要信息。

视频内容片段：
{context}

用户问题：{question}

指导原则：
1. 即使视频内容片段很短或看似不完整，也请尽量从中提取有用信息来回答问题
2. 视频内容片段中的任何文字都可能是有用的线索，请充分利用
3. 如果视频内容片段确实无法回答问题，再说明"视频内容中没有提供相关信息"
4. 绝对不要编造不在视频内容中的信息
5. 回答要简洁、准确、有条理
6. 如果合适，可以引用视频中的具体时间点"""
            
        else:  # 自由对话模式
            prompt = f"""你是一个教育助手。请回答以下问题，提供安全、有帮助、准确的回答：

问题：{question}"""
            
        try:
            # 创建流式聊天完成
            stream = client.chat.completions.create(
                model="qwen-max",
                messages=[
                    {"role": "system", "content": "你是一个教育助手。你会为用户提供安全，有帮助，准确的回答。即使只有很短的信息片段，也要尽量从中提取有用信息来回答问题。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # 增加温度参数，提高创造性
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
