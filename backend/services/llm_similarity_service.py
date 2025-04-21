"""
基于LLM的标签相似度计算服务
"""
import logging
import json
import requests
import traceback
from typing import List, Dict, Any, Tuple, Optional, Union
import os
import re
from openai import OpenAI

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 直接使用固定的API密钥（与semantic_utils.py保持一致）
OPENAI_API_KEY = "sk-178e130a121445659860893fdfae1e7d"
OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# Ollama API配置
OLLAMA_BASE_URL = "http://localhost:11434/api"
OLLAMA_MODEL = "qwen2.5:7b"  # 默认使用qwen2.5:7b模型

class LLMSimilarityService:
    """基于LLM的标签相似度计算服务"""
    
    def __init__(self):
        """初始化LLM相似度服务"""
        self.openai_client = None
        self.use_ollama = False
        self.use_openai = False
        
        # 尝试初始化OpenAI客户端
        try:
            self.openai_client = OpenAI(
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_BASE_URL
            )
            self.use_openai = True
            logger.info("OpenAI客户端初始化成功")
        except Exception as e:
            logger.error(f"OpenAI客户端初始化失败: {str(e)}")
        
        # 检查Ollama服务是否可用
        if self.check_ollama_service():
            self.use_ollama = True
            logger.info("Ollama服务可用")
        else:
            logger.warning("Ollama服务不可用")
            
        # 如果两种LLM都不可用，发出警告
        if not self.use_openai and not self.use_ollama:
            logger.warning("OpenAI和Ollama服务都不可用，将无法使用LLM进行相似度计算")
    
    def check_ollama_service(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"无法连接到Ollama服务: {str(e)}")
            return False
    
    def calculate_tag_similarity_with_llm(self, tag1: str, tag2: str) -> float:
        """
        使用LLM计算两个标签之间的相似度
        
        Args:
            tag1: 第一个标签
            tag2: 第二个标签
            
        Returns:
            相似度分数，范围0-1
        """
        # 如果标签完全相同，直接返回1.0
        if tag1.lower() == tag2.lower():
            return 1.0
            
        # 如果一个标签是另一个的子字符串，给予较高相似度
        if tag1.lower() in tag2.lower() or tag2.lower() in tag1.lower():
            return 0.9
        
        # 尝试使用Ollama（如果可用）
        if self.use_ollama:
            try:
                similarity = self._calculate_similarity_with_ollama(tag1, tag2)
                if similarity is not None:
                    return similarity
            except Exception as e:
                logger.error(f"使用Ollama计算相似度失败: {str(e)}")
        
        # 如果Ollama不可用或失败，尝试使用OpenAI（如果可用）
        if self.use_openai:
            try:
                similarity = self._calculate_similarity_with_openai(tag1, tag2)
                if similarity is not None:
                    return similarity
            except Exception as e:
                logger.error(f"使用OpenAI计算相似度失败: {str(e)}")
        
        # 如果LLM方法都失败，使用简单的字符串相似度计算
        return self._calculate_string_similarity(tag1, tag2)
    
    def _calculate_similarity_with_ollama(self, tag1: str, tag2: str) -> Optional[float]:
        """使用Ollama计算标签相似度"""
        prompt = f"""请判断以下两个标签的语义相似度，返回一个0到1之间的浮点数，其中1表示完全相同，0表示完全不相关。
标签1: {tag1}
标签2: {tag2}

请只返回一个浮点数，不要有任何其他文字。例如: 0.75"""
        
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1
                    }
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API调用失败: {response.status_code} {response.text}")
                return None
                
            response_text = response.json().get("response", "").strip()
            
            # 尝试从响应中提取浮点数
            match = re.search(r'(\d+\.\d+|\d+)', response_text)
            if match:
                similarity = float(match.group(1))
                # 确保相似度在0-1范围内
                similarity = max(0.0, min(1.0, similarity))
                logger.info(f"Ollama计算的标签相似度: {similarity}")
                return similarity
            else:
                logger.warning(f"无法从Ollama响应中提取相似度: {response_text}")
                return None
                
        except Exception as e:
            logger.error(f"Ollama API请求异常: {str(e)}")
            return None
    
    def _calculate_similarity_with_openai(self, tag1: str, tag2: str) -> Optional[float]:
        """使用OpenAI计算标签相似度"""
        if not self.openai_client:
            return None
            
        prompt = f"""请判断以下两个标签的语义相似度，返回一个0到1之间的浮点数，其中1表示完全相同，0表示完全不相关。
标签1: {tag1}
标签2: {tag2}

请只返回一个浮点数，不要有任何其他文字。例如: 0.75"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="qwen-max",  # 使用通义千问大模型
                messages=[
                    {"role": "system", "content": "你是一个专业的语义相似度计算助手。你的任务是判断两个标签之间的语义相似度，并返回一个0到1之间的浮点数。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # 尝试从响应中提取浮点数
            match = re.search(r'(\d+\.\d+|\d+)', response_text)
            if match:
                similarity = float(match.group(1))
                # 确保相似度在0-1范围内
                similarity = max(0.0, min(1.0, similarity))
                logger.info(f"OpenAI计算的标签相似度: {similarity}")
                return similarity
            else:
                logger.warning(f"无法从OpenAI响应中提取相似度: {response_text}")
                return None
                
        except Exception as e:
            logger.error(f"OpenAI API请求异常: {str(e)}")
            return None
    
    def _calculate_string_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度（Jaccard相似度）"""
        if not s1 or not s2:
            return 0.0
            
        # 对于中文，按字符分割；对于英文，按词分割
        if any('\u4e00' <= char <= '\u9fff' for char in s1 + s2):
            set1 = set(s1)
            set2 = set(s2)
        else:
            set1 = set(s1.split())
            set2 = set(s2.split())
            
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_tag_sets_similarity(self, tags1: List[str], tags2: List[str]) -> float:
        """
        计算两组标签之间的相似度
        
        Args:
            tags1: 第一组标签
            tags2: 第二组标签
            
        Returns:
            相似度分数，范围0-1
        """
        if not tags1 or not tags2:
            return 0.0
            
        # 计算最佳匹配的平均相似度
        similarities = []
        
        # 对于tags1中的每个标签，找到tags2中最相似的标签
        for tag1 in tags1:
            best_similarity = max([self.calculate_tag_similarity_with_llm(tag1, tag2) for tag2 in tags2], default=0)
            similarities.append(best_similarity)
        
        # 对于tags2中的每个标签，找到tags1中最相似的标签
        for tag2 in tags2:
            best_similarity = max([self.calculate_tag_similarity_with_llm(tag2, tag1) for tag1 in tags1], default=0)
            similarities.append(best_similarity)
        
        # 计算平均相似度
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def can_combine_knowledge_graphs(self, tags1: List[str], tags2: List[str], threshold: float = 0.7) -> bool:
        """
        判断两组标签是否足够相似，可以合并知识图谱
        
        Args:
            tags1: 第一组标签
            tags2: 第二组标签
            threshold: 相似度阈值，默认0.7
            
        Returns:
            是否可以合并
        """
        similarity = self.calculate_tag_sets_similarity(tags1, tags2)
        logger.info(f"标签组相似度: {similarity}, 阈值: {threshold}")
        return similarity >= threshold
    
    def find_similar_videos(self, target_tags: List[str], all_videos: List[Dict[str, Any]], 
                          threshold: float = 0.7, limit: int = 5) -> List[Dict[str, Any]]:
        """
        查找与目标标签相似的视频
        
        Args:
            target_tags: 目标标签列表
            all_videos: 所有视频数据
            threshold: 相似度阈值，默认0.7
            limit: 返回结果数量限制，默认5
            
        Returns:
            相似视频列表，按相似度降序排序
        """
        if not target_tags or not all_videos:
            return []
            
        similar_videos = []
        
        for video in all_videos:
            video_tags = []
            
            # 获取视频标签
            if video.get('tags'):
                try:
                    if isinstance(video['tags'], str):
                        video_tags = json.loads(video['tags'])
                    else:
                        video_tags = video['tags']
                except json.JSONDecodeError:
                    logger.warning(f"视频 {video.get('id')} 的标签格式无效: {video.get('tags')}")
                    continue
            
            # 如果视频没有标签，跳过
            if not video_tags:
                continue
                
            # 计算相似度
            similarity = self.calculate_tag_sets_similarity(target_tags, video_tags)
            
            # 如果相似度超过阈值，添加到结果列表
            if similarity >= threshold:
                similar_videos.append({
                    'video': video,
                    'similarity': similarity
                })
        
        # 按相似度降序排序
        similar_videos.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 限制返回数量
        return similar_videos[:limit]

# 创建全局实例
llm_similarity_service = LLMSimilarityService()
