"""
检索增强生成（RAG）系统
功能：
1. 实现检索增强生成（RAG）系统
2. 支持基于字幕的相似内容检索
3. 高效的向量检索和相似度计算
4. 支持 GPU 加速

技术：
- 使用 FAISS 进行高效向量检索
- 使用 SentenceTransformer 进行文本向量化
- 实现了余弦相似度计算
- 使用正则表达式处理时间戳
- 支持批量处理和增量更新
"""

import os
import re
import numpy as np
from typing import List, Dict, Tuple, Optional
from flask import current_app
from sentence_transformers import SentenceTransformer

# 尝试导入FAISS，如果不可用则使用备用方案
try:
    import faiss
    FAISS_AVAILABLE = True
    print("成功初始化FAISS")
except ImportError:
    FAISS_AVAILABLE = False
    print("警告: 未找到FAISS模块，将使用备用方案")

# 尝试导入torch，用于GPU加速
try:
    import torch
    TORCH_AVAILABLE = True
    print(f"PyTorch可用，CUDA状态: {torch.cuda.is_available()}")
except ImportError:
    TORCH_AVAILABLE = False
    print("警告: 未找到PyTorch模块，将使用CPU模式")

class RAGSystem:
    """检索增强生成系统类"""
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """初始化RAG系统"""
        # 初始化向量模型
        self.model = SentenceTransformer(model_name)
        # 存储字幕文本和时间戳
        self.subtitles: Dict = {}
        # 存储向量
        self.vectors = None
        # 初始化FAISS索引
        self.index = None
        # 存储文本
        self.texts = []
        # 存储时间戳信息
        self.timestamps = []
        
        # 初始化GPU资源（如果可用）
        self.use_gpu = False
        self.res = None
        
        if FAISS_AVAILABLE and TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                self.res = faiss.StandardGpuResources()
                # 设置临时内存限制为 256MB
                self.res.setTempMemory(256 * 1024 * 1024)
                self.use_gpu = True
                print("FAISS GPU资源初始化成功")
            except Exception as e:
                print(f"FAISS GPU资源初始化失败: {str(e)}")
                self.use_gpu = False
    
    def _create_index(self, dimension):
        """创建FAISS索引"""
        if not FAISS_AVAILABLE:
            print("FAISS模块不可用，无法创建索引")
            return None
            
        try:
            # 先清理之前的索引
            if self.index is not None:
                del self.index
                self.index = None
            
            # 创建CPU索引（使用余弦相似度）
            cpu_index = faiss.IndexFlatIP(dimension)  # 内积用于余弦相似度（向量需要归一化）
            
            if self.use_gpu and self.res is not None:
                try:
                    # 尝试创建GPU索引
                    gpu_index = faiss.index_cpu_to_gpu(self.res, 0, cpu_index)
                    print("成功创建GPU索引")
                    return gpu_index
                except Exception as e:
                    print(f"GPU索引创建失败，回退到CPU索引: {str(e)}")
                    return cpu_index
            else:
                return cpu_index
                
        except Exception as e:
            print(f"索引创建失败: {str(e)}")
            return None

    def _parse_timestamp(self, timestamp_str: str) -> Tuple[Optional[str], Optional[str]]:
        """解析时间戳字符串，返回开始和结束时间"""
        # 尝试解析 [00:00:00 --> 00:00:05] 格式
        match = re.match(r'\[(.*?)\s*-->\s*(.*?)\]', timestamp_str)
        if match:
            return match.group(1).strip(), match.group(2).strip()
            
        # 尝试解析 00:00:00,000 --> 00:00:05,000 格式 (SRT格式)
        match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', timestamp_str)
        if match:
            return match.group(1).strip(), match.group(2).strip()
            
        # 尝试解析 00:00:00 --> 00:00:05 格式
        match = re.match(r'(\d{2}:\d{2}:\d{2})\s*-->\s*(\d{2}:\d{2}:\d{2})', timestamp_str)
        if match:
            return match.group(1).strip(), match.group(2).strip()
            
        return None, None
        
    def _parse_srt_file(self, content: str) -> Tuple[List[str], List[Dict]]:
        """解析SRT格式字幕文件"""
        texts = []
        timestamps = []
        
        # 分割成字幕块
        blocks = re.split(r'\n\s*\n', content)
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
                
            # 第一行是序号，跳过
            # 第二行是时间戳
            timestamp_line = lines[1]
            # 剩余行是文本
            text = ' '.join(lines[2:]).strip()
            
            # 解析时间戳
            start_time, end_time = self._parse_timestamp(timestamp_line)
            if start_time and end_time and text:
                texts.append(text)
                timestamps.append({
                    "start_time": start_time,
                    "end_time": end_time
                })
                
        return texts, timestamps
        
    def _parse_txt_file(self, content: str) -> Tuple[List[str], List[Dict]]:
        """解析自定义格式的TXT字幕文件"""
        texts = []
        timestamps = []
        
        # 将内容分割成段落
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        for p in paragraphs:
            try:
                # 查找时间戳结束位置
                timestamp_end = p.find(']')
                if timestamp_end == -1:
                    # 尝试查找不带方括号的时间戳
                    timestamp_match = re.search(r'(\d{2}:\d{2}:\d{2}(?:,\d{3})?)\s*-->\s*(\d{2}:\d{2}:\d{2}(?:,\d{3})?)', p)
                    if timestamp_match:
                        timestamp_str = timestamp_match.group(0)
                        timestamp_end = p.find(timestamp_str) + len(timestamp_str)
                        text = p[timestamp_end:].strip()
                        start_time, end_time = self._parse_timestamp(timestamp_str)
                    else:
                        continue
                else:
                    timestamp_str = p[:timestamp_end+1]
                    text = p[timestamp_end+1:].strip()
                    start_time, end_time = self._parse_timestamp(timestamp_str)
                
                if start_time and end_time and text:
                    texts.append(text)
                    timestamps.append({
                        "start_time": start_time,
                        "end_time": end_time
                    })
            except Exception as e:
                current_app.logger.error(f"处理段落时出错: {str(e)}")
                continue
                
        return texts, timestamps
        
    def create_knowledge_base(self, subtitle_path: str) -> 'RAGSystem':
        """从字幕文件创建知识库"""
        try:
            if not os.path.exists(subtitle_path):
                raise FileNotFoundError(f"字幕文件不存在: {subtitle_path}")
                
            # 尝试多种编码读取字幕文件
            content = None
            encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin-1']
            
            for encoding in encodings:
                try:
                    with open(subtitle_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    # 检查内容是否有效（不是乱码）
                    if content and not all(ord(c) > 127 for c in content[:100]):
                        current_app.logger.info(f"成功使用 {encoding} 编码读取字幕文件")
                        break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    current_app.logger.error(f"使用 {encoding} 编码读取字幕文件时出错: {str(e)}")
                    continue
            
            if not content:
                raise ValueError(f"无法读取字幕文件，尝试了以下编码: {encodings}")
            
            # 根据文件扩展名选择解析方法
            file_ext = os.path.splitext(subtitle_path)[1].lower()
            if file_ext == '.srt':
                texts, timestamps = self._parse_srt_file(content)
            else:
                # 尝试多种格式解析
                texts, timestamps = self._parse_txt_file(content)
                
                # 如果解析失败，尝试SRT格式解析
                if not texts:
                    texts, timestamps = self._parse_srt_file(content)
                    
                # 如果仍然失败，尝试直接按行分割
                if not texts:
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    if lines:
                        texts = lines
                        timestamps = [{"start_time": "00:00:00", "end_time": "00:00:05"} for _ in lines]
                        current_app.logger.info(f"使用简单行分割方式解析字幕，共 {len(texts)} 行")
            
            if not texts:
                raise ValueError("未找到有效的字幕内容")
            
            # 清空之前的数据
            self.texts = []
            self.timestamps = []
            self.vectors = None
            self.index = None
            
            # 计算文本向量
            if TORCH_AVAILABLE and torch.cuda.is_available():
                with torch.device('cuda'):
                    vectors = self.model.encode(texts, convert_to_tensor=True)
                    # L2归一化，用于余弦相似度
                    vectors = torch.nn.functional.normalize(vectors, p=2, dim=1)
                    vectors = vectors.cpu().numpy().astype('float32')
            else:
                vectors = self.model.encode(texts)
                # L2归一化，用于余弦相似度
                vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
                vectors = vectors.astype('float32')
            
            # 更新文本和时间戳列表
            self.texts.extend(texts)
            self.timestamps.extend(timestamps)
            self.vectors = vectors
            
            # 创建索引
            if FAISS_AVAILABLE:
                dimension = vectors.shape[1]
                self.index = self._create_index(dimension)
                
                if self.index is not None:
                    self.index.add(vectors)
                    current_app.logger.info(f"成功添加 {len(texts)} 个段落到索引")
                else:
                    current_app.logger.warning("索引创建失败，无法添加向量")
            
            return self
                
        except Exception as e:
            current_app.logger.error(f"创建知识库失败: {str(e)}")
            import traceback
            current_app.logger.error(f"错误详情: {traceback.format_exc()}")
            raise
    
    def search_similar_segments(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索与查询最相似的片段"""
        if not self.texts:
            raise ValueError("知识库未初始化")
            
        # 将查询转换为向量
        if TORCH_AVAILABLE and torch.cuda.is_available():
            with torch.device('cuda'):
                query_vector = self.model.encode([query], convert_to_tensor=True)
                query_vector = torch.nn.functional.normalize(query_vector, p=2, dim=1)
                query_vector = query_vector.cpu().numpy().astype('float32')
        else:
            query_vector = self.model.encode([query])
            query_vector = query_vector / np.linalg.norm(query_vector, axis=1, keepdims=True)
            query_vector = query_vector.astype('float32')
        
        # 搜索最相似的片段
        results = []
        
        if FAISS_AVAILABLE and self.index is not None:
            # 使用FAISS搜索
            # 增加检索数量，提高覆盖率
            search_k = min(top_k * 2, len(self.texts))  # 搜索更多结果，但不超过总文本数量
            similarities, indices = self.index.search(query_vector, search_k)
            
            # 过滤低相似度的结果
            min_similarity_threshold = 0.3  # 降低相似度阈值，增加召回率
            
            filtered_results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.texts) and similarities[0][i] >= min_similarity_threshold:
                    filtered_results.append({
                        'text': self.texts[idx],
                        'timestamp': self.timestamps[idx],
                        'score': float(similarities[0][i])
                    })
            
            # 如果过滤后的结果太少，放宽限制
            if len(filtered_results) < 2:
                results = [{
                    'text': self.texts[idx],
                    'timestamp': self.timestamps[idx],
                    'score': float(similarities[0][i])
                } for i, idx in enumerate(indices[0][:top_k]) if idx < len(self.texts)]
            else:
                # 限制返回结果数量
                results = filtered_results[:top_k]
        else:
            # 备用方案：计算余弦相似度
            if self.vectors is not None:
                similarities = np.dot(query_vector, self.vectors.T)[0]
                # 增加检索数量
                search_k = min(top_k * 2, len(self.texts))
                top_indices = np.argsort(similarities)[-search_k:][::-1]
                
                # 过滤低相似度的结果
                min_similarity_threshold = 0.3
                
                filtered_results = []
                for idx in top_indices:
                    if similarities[idx] >= min_similarity_threshold:
                        filtered_results.append({
                            'text': self.texts[idx],
                            'timestamp': self.timestamps[idx],
                            'score': float(similarities[idx])
                        })
                
                # 如果过滤后的结果太少，放宽限制
                if len(filtered_results) < 2:
                    results = [{
                        'text': self.texts[idx],
                        'timestamp': self.timestamps[idx],
                        'score': float(similarities[idx])
                    } for idx in top_indices[:top_k]]
                else:
                    # 限制返回结果数量
                    results = filtered_results[:top_k]
            else:
                # 如果没有向量，返回前几个文档
                for i, text in enumerate(self.texts[:top_k]):
                    results.append({
                        'text': text,
                        'timestamp': self.timestamps[i],
                        'score': 0.0  # 无法计算相似度分数
                    })
                
        return results
