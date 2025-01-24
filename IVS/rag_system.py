import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import json
import os
import torch
import re

class RAGSystem:
    def __init__(self):
        # 初始化向量模型
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        if torch.cuda.is_available():
            self.model = self.model.to(torch.device('cuda'))
        
        # 初始化FAISS索引 - 使用余弦相似度
        self.index = None
        # 存储字幕文本和时间戳
        self.subtitles: List[Dict] = []
        # 字幕文件路径
        self.captions_dir = "captions"

    def _create_gpu_index(self, dim):
        """创建GPU索引，使用内积（对于归一化向量相当于余弦相似度）"""
        # 创建使用内积的CPU索引
        cpu_index = faiss.IndexFlatIP(dim)
        
        # 将索引转移到GPU
        if torch.cuda.is_available():
            # 获取GPU资源
            res = faiss.StandardGpuResources()
            # 转移到GPU
            gpu_index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
            return gpu_index
        return cpu_index
    
    def _parse_timestamp(self, timestamp_str: str) -> Tuple[str, str]:
        """解析时间戳字符串，返回开始和结束时间"""
        match = re.match(r'\[(.*?)\s*-->\s*(.*?)\]', timestamp_str)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return None, None
        
    def add_subtitles_from_txt(self, video_id: str, txt_file_path: str):
        """从TXT文件添加字幕到RAG系统"""
        self._ensure_captions_dir()
        
        # 读取TXT文件
        subtitles = []
        texts = []
        
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                # 提取时间戳和文本
                timestamp_end = line.find(']')
                if timestamp_end == -1:
                    continue
                    
                timestamp_str = line[:timestamp_end+1]
                text = line[timestamp_end+1:].strip()
                
                start_time, end_time = self._parse_timestamp(timestamp_str)
                if start_time and end_time:
                    subtitle = {
                        "start_time": start_time,
                        "end_time": end_time,
                        "text": text
                    }
                    subtitles.append(subtitle)
                    texts.append(text)
        
        if not subtitles:
            return False
            
        # 更新字幕列表
        self.subtitles = subtitles
        
        # 生成文本向量并归一化
        with torch.device('cuda' if torch.cuda.is_available() else 'cpu'):
            vectors = self.model.encode(texts, convert_to_tensor=True)
            vectors = torch.nn.functional.normalize(vectors, p=2, dim=1)  # L2归一化
            vectors = vectors.cpu().numpy()
        
        # 创建或更新FAISS索引
        if self.index is None:
            self.index = self._create_gpu_index(vectors.shape[1])
        else:
            self.index.reset()
        self.index.add(vectors.astype(np.float32))
        
        return True
    
    def search_similar_subtitles(self, query: str, top_k: int = 3) -> List[Dict]:
        """搜索与问题最相关的字幕"""
        if not self.subtitles or self.index is None:
            return []
            
        # 将查询转换为向量并归一化
        with torch.device('cuda' if torch.cuda.is_available() else 'cpu'):
            query_vector = self.model.encode([query], convert_to_tensor=True)
            query_vector = torch.nn.functional.normalize(query_vector, p=2, dim=1)  # L2归一化
            query_vector = query_vector.cpu().numpy()
        
        # 搜索最相似的字幕
        similarities, indices = self.index.search(query_vector.astype(np.float32), top_k)
        
        # 获取相关字幕和分数
        similar_subtitles = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.subtitles):
                subtitle = self.subtitles[idx].copy()
                # 余弦相似度范围为[-1, 1]，我们将其映射到[0, 1]
                similarity_score = float((similarities[0][i] + 1) / 2)
                subtitle['similarity_score'] = similarity_score
                similar_subtitles.append(subtitle)
        
        # 按相似度分数排序
        similar_subtitles.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar_subtitles
    
    def load_subtitles(self, video_id: str) -> bool:
        """加载指定视频的TXT字幕"""
        txt_file = os.path.join(self.captions_dir, f"{video_id}.txt")
        if not os.path.exists(txt_file):
            return False
            
        return self.add_subtitles_from_txt(video_id, txt_file)
        
    def _ensure_captions_dir(self):
        """确保字幕目录存在"""
        if not os.path.exists(self.captions_dir):
            os.makedirs(self.captions_dir)
