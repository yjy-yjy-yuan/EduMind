"""
智能聊天系统
功能：
1. 实现智能聊天系统，用于与用户进行教育相关的对话
2. 包含对话历史记录管理
3. 集成上下文感知能力
4. 支持两种模式：基于视频内容的RAG问答和自由问答

技术：
- 使用 OpenAI API（通义千问模型）进行对话生成
- 采用异步流式处理技术
- 使用 typing 模块进行类型提示
- 实现上下文管理和历史记录维护
- 集成RAG系统进行基于视频内容的问答
"""

from typing import List, Dict, Optional, Generator, Union
from openai import OpenAI
from flask import current_app
from .rag_system import RAGSystem

class ChatSystem:
    """智能聊天系统类"""
    
    def __init__(self):
        """初始化聊天系统"""
        # 分别为两种模式维护独立的历史记录
        self.free_history: List[Dict] = []
        self.video_history: List[Dict] = []
        
        # 初始化通义千问客户端
        self.client = OpenAI(
            api_key = "sk-59a6a7690bfb42cd887365795e114002",
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        # 添加系统角色设置
        self.free_history.append({
            "role": "system",
            "content": "你是一个教育助手。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。"
        })
        
        self.video_history.append({
            "role": "system",
            "content": "你是一个基于视频内容的教育助手。你会根据视频内容为用户提供安全，有帮助，准确的回答。如果问题无法从视频内容中得到答案，请明确告知用户。"
        })
        
        # 初始化RAG系统
        self.rag_system = RAGSystem()

    def chat(self, message: str, mode: str = "free", context: Optional[str] = None, rag_system: Optional[RAGSystem] = None) -> Generator[str, None, None]:
        """
        处理用户消息并返回响应（流式）
        
        Args:
            message: 用户消息
            mode: 对话模式，"free"为自由对话，"video"为基于视频内容的问答
            context: 可选的上下文信息（如视频字幕内容）
            rag_system: 可选的RAG系统实例，用于基于视频内容的问答
            
        Returns:
            生成器，逐步返回回答内容
        """
        try:
            # 准备发送到API的消息
            messages = self._prepare_messages(message, mode, context, rag_system)
            
            # 创建流式对话
            stream = self.client.chat.completions.create(
                model="qwen-turbo",
                messages=messages,
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
            
            # 添加助手响应到对应模式的历史记录
            if mode == "video":
                self.video_history.append({"role": "assistant", "content": full_response})
            else:
                self.free_history.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            error_msg = f"对话生成出错: {str(e)}"
            current_app.logger.error(error_msg)
            
            # 添加错误消息到对应模式的历史记录
            if mode == "video":
                self.video_history.append({"role": "assistant", "content": error_msg})
            else:
                self.free_history.append({"role": "assistant", "content": error_msg})
                
            yield error_msg
    
    def _prepare_messages(self, message: str, mode: str, context: Optional[str], rag_system: Optional[RAGSystem]) -> List[Dict]:
        """
        准备发送给API的消息列表
        
        Args:
            message: 用户消息
            mode: 对话模式
            context: 可选的上下文信息
            rag_system: 可选的RAG系统实例
            
        Returns:
            消息列表
        """
        messages = []
        
        # 根据模式选择对应的历史记录
        history = self.video_history if mode == "video" else self.free_history
        
        # 添加系统消息
        if mode == "video" and rag_system is not None:
            # 使用RAG系统检索相关内容
            try:
                similar_segments = rag_system.search_similar_segments(message, top_k=3)
                if similar_segments:
                    rag_context = "\n\n".join([f"[{seg['timestamp']['start_time']} --> {seg['timestamp']['end_time']}] {seg['text']}" for seg in similar_segments])
                    system_message = f"你是一个教育助手。请基于以下视频内容回答问题。如果问题无法从内容中得到答案，请说明无法回答。\n\n视频内容：\n{rag_context}"
                    messages.append({"role": "system", "content": system_message})
                else:
                    messages.append({"role": "system", "content": "你是一个教育助手。请基于视频内容回答问题。但目前没有找到与问题相关的视频内容，请告知用户。"})
            except Exception as e:
                current_app.logger.error(f"RAG检索出错: {str(e)}")
                messages.append({"role": "system", "content": "你是一个教育助手。请基于视频内容回答问题。但检索系统出现错误，请告知用户。"})
        elif mode == "video" and context:
            # 使用提供的上下文
            messages.append({
                "role": "system",
                "content": f"你是一个教育助手。请基于以下视频内容回答问题：\n\n{context}"
            })
        else:
            # 自由对话模式，使用初始化时设置的系统消息
            messages.append(history[0])
        
        # 添加历史对话（最多保留最近5轮对话）
        recent_history = history[1:11] if len(history) > 11 else history[1:]
        messages.extend(recent_history)
        
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        
        # 将当前用户消息添加到对应模式的历史记录
        if mode == "video":
            self.video_history.append({"role": "user", "content": message})
        else:
            self.free_history.append({"role": "user", "content": message})
        
        return messages
    
    def get_history(self, mode: str = "free") -> List[Dict]:
        """获取对话历史"""
        return self.video_history if mode == "video" else self.free_history
    
    def clear_history(self, mode: str = "free") -> None:
        """清空对话历史"""
        if mode == "video":
            # 保留视频模式的系统角色设置
            system_message = self.video_history[0]
            self.video_history = [system_message]
        else:
            # 保留自由模式的系统角色设置
            system_message = self.free_history[0]
            self.free_history = [system_message]
        
    def clear_all_history(self) -> None:
        """清空所有对话历史"""
        # 保留系统角色设置
        free_system_message = self.free_history[0]
        video_system_message = self.video_history[0]
        self.free_history = [free_system_message]
        self.video_history = [video_system_message]
    
    def add_user_message(self, message: str, mode: str = "free") -> None:
        """添加用户消息到历史记录"""
        if mode == "video":
            self.video_history.append({"role": "user", "content": message})
        else:
            self.free_history.append({"role": "user", "content": message})
