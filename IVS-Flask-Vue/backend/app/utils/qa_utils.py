import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import re
from typing import List, Dict, Tuple

class QASystem:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        # 初始化向量模型
        self.model = SentenceTransformer(model_name)
        # 初始化 FAISS 资源
        try:
            self.res = faiss.StandardGpuResources()
            # 设置临时内存限制为 256MB
            self.res.setTempMemory(256 * 1024 * 1024)
            self.use_gpu = True
            print("成功初始化GPU资源")
        except Exception as e:
            print(f"GPU资源初始化失败，将使用CPU: {str(e)}")
            self.use_gpu = False
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
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 将内容分割成段落
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # 提取文本内容和时间戳
        texts = []
        timestamps = []
        for p in paragraphs:
            try:
                timestamp_end = p.find(']')
                if timestamp_end == -1:
                    continue
                
                timestamp_str = p[:timestamp_end+1]
                text = p[timestamp_end+1:].strip()
                
                start_time, end_time = self._parse_timestamp(timestamp_str)
                if start_time and end_time:
                    texts.append(text)
                    timestamps.append({
                        "start_time": start_time,
                        "end_time": end_time
                    })
            except Exception as e:
                print(f"处理段落时出错: {str(e)}")
                continue
                
        if not texts:
            raise ValueError("未找到有效的字幕内容")
            
        # 将文本转换为向量
        vectors = self.model.encode(texts)
        vectors = vectors.astype('float32')
        
        # 创建索引
        dimension = vectors.shape[1]
        self.index = self._create_index(dimension)
        if self.index is None:
            raise RuntimeError("无法创建索引")
            
        # 添加向量到索引
        self.index.add(vectors)
        
        # 保存文本和时间戳
        self.texts = texts
        self.timestamps = timestamps
        self.vectors = vectors
        
        return self
        
    def search_similar_segments(self, query: str, top_k: int = 3) -> List[Dict]:
        """搜索与查询最相似的片段"""
        if not self.index or not self.texts:
            raise ValueError("知识库未初始化")
            
        # 将查询转换为向量
        query_vector = self.model.encode([query])
        query_vector = query_vector.astype('float32')
        
        # 搜索最相似的片段
        distances, indices = self.index.search(query_vector, top_k)
        
        # 返回结果
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.texts):
                results.append({
                    'text': self.texts[idx],
                    'timestamp': self.timestamps[idx],
                    'score': float(distances[0][i])
                })
                
        return results
        
    def get_answer(self, question: str, api_key: str, mode: str = 'video', context: str = None) -> str:
        """获取问题的答案"""
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
