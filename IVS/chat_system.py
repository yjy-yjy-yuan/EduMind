# chat_system.py
# 实现了一个简单的聊天系统，用于与用户进行对话，并记录对话历史。

from typing import List, Dict, Optional

class ChatSystem:
    # 初始化聊天系统
    def __init__(self):
        self.history: List[Dict] = []
        self.API_KEY = "fg1cy9Y0hRLo2kPoy6WzeP7H"  # 替换为实际的API密钥

    # 处理用户消息并返回响应
    def chat(self, message: str, context: Optional[str] = None) -> str:     
        # 添加用户消息到历史记录
        self.history.append({"role": "user", "content": message})
        
        try:
            # 准备发送到API的消息
            messages = self._prepare_messages(message, context)
            
            # 调用API获取响应
            response = self._call_api(messages)
            
            # 添加助手响应到历史记录
            self.history.append({"role": "assistant", "content": response})
            
            return response
            
        except Exception as e:
            error_msg = f"对话生成出错: {str(e)}"
            self.history.append({"role": "assistant", "content": error_msg})
            return error_msg
    
    # 准备发送给API的消息列史
    def _prepare_messages(self, message: str, context: Optional[str]) -> List[Dict]:
        messages = []
        
        # 添加系统消息
        if context:
            messages.append({
                "role": "system",
                "content": f"你是一个教育助手。请基于以下视频内容回答问题：\n\n{context}"
            })
        else:
            messages.append({
                "role": "system",
                "content": "你是一个教育助手。请回答用户的问题。"
            })
        
        # 添加历史对话
        messages.extend(self.history[-5:])  # 只保留最近5条对话
        
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        
        return messages
    
    # 调用API获取响应
    def _call_api(self, messages: List[Dict]) -> str:
        # 这里实现实际的API调用
        # 示例使用本地模拟响应
        return f"这是对消息的回复: {messages[-1]['content']}"
    
    # 获取对话历史
    def get_history(self) -> List[Dict]:
        return self.history
    
    # 清空对话历史
    def clear_history(self) -> None:
        self.history = []
