"""
智能问答系统，实现两种问答模式：
1. 基于视频内容的RAG问答：使用FAISS向量化处理字幕，结合上下文进行回答
2. 自由问答：使用通义千问API进行对话
"""

from typing import List, Dict, Optional
import os
import json
import faiss
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from app.models.video import Video
from app.utils.logger import logger
from app.utils.subtitle_utils import parse_srt_file

class ChatSystem:
    def __init__(self):
        self.history: List[Dict] = []
        # 初始化通义千问客户端
        self.client = OpenAI(
            api_key = "sk-178e130a121445659860893fdfae1e7d",
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        # 初始化sentence transformer模型
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        # 添加系统角色设置
        self.history.append({
            "role": "system",
            "content": "你是一个教育助手。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。"
        })

    def _prepare_messages(self, message: str, context: Optional[str] = None) -> List[Dict]:
        """准备发送给API的消息列表"""
        messages = []
        
        # 添加系统消息
        if context:
            messages.append({
                "role": "system",
                "content": f"你是一个教育助手。请基于以下视频内容回答问题：\n\n{context}"
            })
        else:
            # 使用初始化时设置的系统消息
            messages.append(self.history[0])
        
        # 添加历史对话
        messages.extend(self.history[1:])  # 排除系统消息后的所有历史记录
        
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        
        return messages

    def _process_subtitles(self, subtitles: List[Dict]) -> List[Dict]:
        """处理字幕，优化格式并保留时间戳"""
        processed_subtitles = []
        for sub in subtitles:
            # 合并相邻的短句
            if processed_subtitles and len(processed_subtitles[-1]['text'].split()) < 5:
                processed_subtitles[-1]['text'] += ' ' + sub['text']
                processed_subtitles[-1]['end_time'] = sub['end_time']
            else:
                processed_subtitles.append({
                    'text': sub['text'],
                    'start_time': sub['start_time'],
                    'end_time': sub['end_time']
                })
        return processed_subtitles

    def _build_faiss_index(self, subtitles: List[Dict]) -> tuple:
        """构建FAISS索引"""
        texts = [sub['text'] for sub in subtitles]
        embeddings = self.encoder.encode(texts)
        
        # 创建FAISS索引
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings.astype(np.float32))
        
        return index, embeddings

    def _get_relevant_context(self, question: str, index: faiss.Index, subtitles: List[Dict], k: int = 3) -> str:
        """获取与问题最相关的上下文"""
        # 编码问题
        question_embedding = self.encoder.encode([question])[0].reshape(1, -1)
        
        # 搜索最相关的片段
        D, I = index.search(question_embedding.astype(np.float32), k)
        
        # 构建上下文
        context_parts = []
        for idx in I[0]:
            sub = subtitles[idx]
            context_parts.append(f"[{sub['start_time']} - {sub['end_time']}] {sub['text']}")
        
        return "\n".join(context_parts)

    def chat_with_video(self, message: str, video_id: int) -> str:
        """基于视频内容的问答"""
        try:
            # 获取视频字幕
            video = Video.query.get(video_id)
            if not video or not video.subtitle_filepath:
                raise ValueError("视频字幕不存在")

            logger.info(f"处理视频字幕文件: {video.subtitle_filepath}")

            # 读取并解析字幕文件
            subtitles = parse_srt_file(video.subtitle_filepath)
            if not subtitles:
                raise ValueError("字幕文件解析失败")

            # 处理字幕
            processed_subtitles = self._process_subtitles(subtitles)
            if not processed_subtitles:
                raise ValueError("字幕处理失败")

            logger.info(f"成功处理字幕，共{len(processed_subtitles)}条")
            
            # 构建FAISS索引
            index, _ = self._build_faiss_index(processed_subtitles)
            
            # 获取相关上下文
            context = self._get_relevant_context(message, index, processed_subtitles)
            logger.info(f"找到相关上下文: {context}")
            
            # 准备消息
            messages = self._prepare_messages(message, context)
            
            # 创建对话
            response = self.client.chat.completions.create(
                model="qwen-turbo",
                messages=messages,
                temperature=0.3
            )
            
            # 添加助手响应到历史记录
            answer = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": answer})
            
            return answer
            
        except Exception as e:
            error_msg = f"视频问答出错: {str(e)}"
            logger.error(error_msg)
            self.history.append({"role": "assistant", "content": error_msg})
            return error_msg

    def chat_free(self, message: str) -> str:
        """自由问答模式"""
        try:
            # 准备消息
            messages = self._prepare_messages(message)
            
            # 创建对话
            response = self.client.chat.completions.create(
                model="qwen-turbo",
                messages=messages,
                temperature=0.3
            )
            
            # 添加助手响应到历史记录
            self.history.append({"role": "assistant", "content": response.choices[0].message.content})
            
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = f"自由问答出错: {str(e)}"
            logger.error(error_msg)
            self.history.append({"role": "assistant", "content": error_msg})
            return error_msg

    def get_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.history
    
    def clear_history(self) -> None:
        """清空对话历史"""
        # 保留系统角色设置
        system_message = self.history[0]
        self.history = [system_message]
