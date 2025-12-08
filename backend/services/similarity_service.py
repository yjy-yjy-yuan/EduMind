"""
标签相似度计算和知识图谱整合服务
"""

import json
import logging
import os
import re
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import jieba
import numpy as np
from gensim.models import KeyedVectors

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimilarityService:
    """标签相似度计算和知识图谱整合服务"""

    def __init__(self):
        """初始化相似度服务"""
        self.word_vectors = None
        self.use_word_vectors = False

        # 尝试加载词向量模型
        try:
            # 加载中文词向量模型（如果有）
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', 'sgns.wiki.word'
            )
            if os.path.exists(model_path):
                logger.info(f"正在加载词向量模型: {model_path}")
                self.word_vectors = KeyedVectors.load_word2vec_format(model_path, binary=False)
                self.use_word_vectors = True
                logger.info("词向量模型加载成功")
            else:
                logger.warning(f"词向量模型文件不存在: {model_path}，将使用简单字符串匹配")
        except Exception as e:
            logger.error(f"加载词向量模型失败: {str(e)}")
            logger.info("将使用简单字符串匹配")

    def _preprocess_tag(self, tag: str) -> str:
        """预处理标签文本"""
        # 转为小写，移除特殊字符
        tag = tag.lower()
        tag = re.sub(r'[^\w\s\u4e00-\u9fff]', '', tag)
        return tag.strip()

    def _get_word_vector(self, word: str) -> Optional[np.ndarray]:
        """获取词向量"""
        if not self.use_word_vectors:
            return None

        try:
            if word in self.word_vectors:
                return self.word_vectors[word]

            # 对于中文，尝试分词并取平均
            if any('\u4e00' <= char <= '\u9fff' for char in word):
                words = list(jieba.cut(word))
                vectors = [self.word_vectors[w] for w in words if w in self.word_vectors]
                if vectors:
                    return np.mean(vectors, axis=0)

            return None
        except Exception as e:
            logger.error(f"获取词向量失败: {str(e)}")
            return None

    def calculate_tag_similarity(self, tag1: str, tag2: str) -> float:
        """
        计算两个标签之间的相似度

        Args:
            tag1: 第一个标签
            tag2: 第二个标签

        Returns:
            相似度分数，范围0-1
        """
        # 预处理标签
        tag1 = self._preprocess_tag(tag1)
        tag2 = self._preprocess_tag(tag2)

        # 如果标签完全相同，直接返回1.0
        if tag1 == tag2:
            return 1.0

        # 如果一个标签是另一个的子字符串，给予较高相似度
        if tag1 in tag2 or tag2 in tag1:
            return 0.9

        # 使用词向量计算相似度
        if self.use_word_vectors:
            vec1 = self._get_word_vector(tag1)
            vec2 = self._get_word_vector(tag2)

            if vec1 is not None and vec2 is not None:
                # 计算余弦相似度
                similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
                return float(similarity)

        # 回退到字符级别的相似度计算
        return self._calculate_string_similarity(tag1, tag2)

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
            best_similarity = max([self.calculate_tag_similarity(tag1, tag2) for tag2 in tags2], default=0)
            similarities.append(best_similarity)

        # 对于tags2中的每个标签，找到tags1中最相似的标签
        for tag2 in tags2:
            best_similarity = max([self.calculate_tag_similarity(tag2, tag1) for tag1 in tags1], default=0)
            similarities.append(best_similarity)

        # 计算平均相似度
        return sum(similarities) / len(similarities) if similarities else 0.0

    def can_combine_knowledge_graphs(
        self, video1_tags: List[str], video2_tags: List[str], threshold: float = 0.7
    ) -> bool:
        """
        判断两个视频的知识图谱是否可以结合

        Args:
            video1_tags: 第一个视频的标签列表
            video2_tags: 第二个视频的标签列表
            threshold: 相似度阈值，默认0.7

        Returns:
            是否可以结合
        """
        # 计算标签集合的相似度
        similarity = self.calculate_tag_sets_similarity(video1_tags, video2_tags)
        logger.info(f"视频标签相似度: {similarity}, 阈值: {threshold}")

        # 判断是否超过阈值
        return similarity >= threshold

    def find_similar_videos(
        self, target_tags: List[str], all_videos: List[Dict[str, Any]], threshold: float = 0.6, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        查找与目标标签相似的视频

        Args:
            target_tags: 目标标签列表
            all_videos: 所有视频的列表，每个视频是一个字典，包含id和tags字段
            threshold: 相似度阈值，默认0.6
            limit: 返回结果的最大数量，默认5

        Returns:
            相似视频列表，按相似度降序排序
        """
        if not target_tags or not all_videos:
            return []

        similar_videos = []

        for video in all_videos:
            # 获取视频标签
            video_tags = []
            if 'tags' in video and video['tags']:
                try:
                    if isinstance(video['tags'], str):
                        video_tags = json.loads(video['tags'])
                    else:
                        video_tags = video['tags']
                except Exception as e:
                    logger.error(f"解析视频标签失败: {str(e)}")
                    continue

            # 计算相似度
            similarity = self.calculate_tag_sets_similarity(target_tags, video_tags)

            # 如果相似度超过阈值，添加到结果列表
            if similarity >= threshold:
                similar_videos.append({'video': video, 'similarity': similarity})

        # 按相似度降序排序
        similar_videos.sort(key=lambda x: x['similarity'], reverse=True)

        # 限制返回数量
        return similar_videos[:limit]


# 创建单例实例
similarity_service = SimilarityService()
