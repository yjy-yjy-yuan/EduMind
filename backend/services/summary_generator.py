"""
视频摘要生成服务
使用ollama模型或在线API处理视频字幕，生成内容摘要
"""

import os
import json
import requests
import logging
import traceback
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ollama API配置
OLLAMA_BASE_URL = "http://localhost:11434/api"
OLLAMA_MODEL = "deepseek-r1:8b"  # 使用deepseek-r1:8b模型

# 在线API配置
OPENAI_API_KEY = "sk-178e130a121445659860893fdfae1e7d"
OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

def check_ollama_service():
    """检查Ollama服务是否可用"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/tags", timeout=5)
        if response.status_code == 200:
            logger.info("Ollama服务正在运行")
            return True
        else:
            logger.warning(f"Ollama服务返回错误状态码: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"无法连接到Ollama服务: {str(e)}")
        return False

class SummaryGenerator:
    """视频摘要生成器，使用ollama模型或在线API处理字幕生成摘要"""
    
    def __init__(self):
        """初始化摘要生成器"""
        # 检查Ollama服务是否可用
        self.use_ollama = check_ollama_service()
        if self.use_ollama:
            logger.info(f"将使用本地Ollama模型: {OLLAMA_MODEL}")
        else:
            logger.info("Ollama服务不可用，将使用在线API")
    
    def _prepare_prompt(self, subtitle_text: str) -> str:
        """
        准备提示词
        
        Args:
            subtitle_text: 字幕文本
            
        Returns:
            格式化后的提示词
        """
        # 这里可以根据需要调整提示词模板
        prompt = f"""你是一个专业的教育视频内容分析助手。请根据以下视频字幕内容，提供一个简洁的摘要（200字以内），概括视频的主要内容、关键知识点和教学目标。
        
字幕内容:
```
{subtitle_text}
```

请提供一个结构化的摘要，包括：
1. 视频主题
2. 核心知识点（3-5点）
3. 适合的学习人群

格式要求：
- 总字数控制在200字以内
- 使用简洁、专业的语言
- 不要重复字幕原文
- 直接输出摘要内容，不要包含"摘要："等前缀
"""
        return prompt
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        调用ollama API生成摘要
        
        Args:
            prompt: 提示词
            
        Returns:
            生成的摘要文本，如果失败则返回None
        """
        try:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
            logger.info(f"调用ollama API生成摘要，模型: {OLLAMA_MODEL}")
            response = requests.post(f"{OLLAMA_BASE_URL}/generate", json=payload, timeout=60)
            
            if response.status_code != 200:
                logger.error(f"ollama API调用失败: {response.status_code}, {response.text}")
                return None
                
            result = response.json()
            summary = result.get("response", "").strip()
            logger.info(f"Ollama生成的摘要: {summary[:50]}...")
            return summary
            
        except Exception as e:
            logger.error(f"调用ollama API时发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def _call_online_api(self, prompt: str) -> Optional[str]:
        """
        调用在线API生成摘要
        
        Args:
            prompt: 提示词
            
        Returns:
            生成的摘要文本，如果失败则返回None
        """
        try:
            # 使用兼容OpenAI的API接口
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            }
            
            payload = {
                "model": "deepseek-r1",  # 使用deepseek-r1模型
                "messages": [
                    {"role": "system", "content": "你是一个专业的教育视频内容分析助手，擅长提炼视频内容要点并生成简洁的摘要。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }
            
            logger.info("调用在线API生成摘要")
            response = requests.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"在线API调用失败: {response.status_code}, {response.text}")
                return None
            
            result = response.json()
            summary = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logger.info(f"在线API生成的摘要: {summary[:50]}...")
            return summary
            
        except Exception as e:
            logger.error(f"调用在线API时发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def _clean_subtitle_text(self, subtitle_text: str) -> str:
        """
        清理字幕文本，移除时间戳和序号
        
        Args:
            subtitle_text: 原始字幕文本
            
        Returns:
            清理后的纯文本
        """
        if not subtitle_text or len(subtitle_text.strip()) == 0:
            logger.error(f"字幕文本为空或只包含空白字符")
            return ""
            
        logger.info(f"原始字幕文本长度: {len(subtitle_text)} 字符，前100个字符: {subtitle_text[:100]}")
        
        # 判断字幕格式（SRT或VTT）
        if "-->" in subtitle_text:
            # 处理SRT格式
            import re
            
            # 使用正则表达式匹配SRT格式的内容部分
            # 匹配模式: 数字序号、时间戳行（包含 -->），然后捕获实际文本内容直到下一个序号或文件结束
            pattern = r'\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}\s*\n(.*?)(?=\n\s*\d+\s*\n|\Z)'
            matches = re.findall(pattern, subtitle_text, re.DOTALL)
            
            if matches:
                # 合并所有匹配到的文本，并清理多余的空白字符
                cleaned_text = ' '.join([re.sub(r'\s+', ' ', match.strip()) for match in matches])
                logger.info(f"正则表达式处理后SRT文本长度: {len(cleaned_text)} 字符，前100个字符: {cleaned_text[:100] if cleaned_text else '空'}")
                return cleaned_text
            
            # 如果正则表达式方法失败，尝试使用行分割方法
            logger.warning("正则表达式处理SRT失败，尝试使用行分割方法")
            lines = subtitle_text.split('\n')
            cleaned_lines = []
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # 跳过空行
                if not line:
                    i += 1
                    continue
                    
                # 跳过序号行（纯数字）
                if line.isdigit():
                    i += 1
                    continue
                    
                # 跳过时间戳行
                if "-->" in line:
                    i += 1
                    continue
                    
                # 添加字幕文本
                cleaned_lines.append(line)
                i += 1
            
            result = " ".join(cleaned_lines)
            logger.info(f"行分割方法处理后SRT文本长度: {len(result)} 字符，前100个字符: {result[:100] if result else '空'}")
            return result
        else:
            # 尝试其他常见字幕格式处理
            # 1. 移除可能的XML/HTML标签
            import re
            text_without_tags = re.sub(r'<[^>]+>', ' ', subtitle_text)
            
            # 2. 移除多余的空白字符
            text_cleaned = re.sub(r'\s+', ' ', text_without_tags).strip()
            
            logger.info(f"非SRT格式处理后文本长度: {len(text_cleaned)} 字符，前100个字符: {text_cleaned[:100] if text_cleaned else '空'}")
            
            # 如果处理后文本太短，可能是格式无法识别，直接返回原文本
            if len(text_cleaned) < 50 and len(subtitle_text.strip()) > 50:
                logger.warning("处理后文本太短，返回原始文本")
                return subtitle_text.strip()
                
            return text_cleaned
    
    def generate_summary(self, subtitle_path: str) -> Dict[str, Any]:
        """
        从字幕文件生成视频摘要
        
        Args:
            subtitle_path: 字幕文件路径（SRT或VTT格式）
            
        Returns:
            包含摘要和状态的字典
        """
        try:
            # 检查字幕文件是否存在
            if not os.path.exists(subtitle_path):
                logger.error(f"字幕文件不存在: {subtitle_path}")
                return {"success": False, "error": "字幕文件不存在", "summary": None}
            
            # 获取文件大小
            file_size = os.path.getsize(subtitle_path)
            logger.info(f"字幕文件大小: {file_size} 字节")
            
            if file_size == 0:
                logger.error(f"字幕文件为空: {subtitle_path}")
                return {"success": False, "error": "字幕文件为空", "summary": None}
            
            # 读取字幕文件
            try:
                with open(subtitle_path, 'r', encoding='utf-8') as f:
                    subtitle_text = f.read()
            except UnicodeDecodeError:
                # 尝试其他编码
                logger.warning(f"UTF-8编码读取失败，尝试其他编码")
                try:
                    with open(subtitle_path, 'r', encoding='gbk') as f:
                        subtitle_text = f.read()
                except UnicodeDecodeError:
                    try:
                        with open(subtitle_path, 'r', encoding='latin-1') as f:
                            subtitle_text = f.read()
                    except Exception as e:
                        logger.error(f"所有编码尝试均失败: {str(e)}")
                        return {"success": False, "error": "无法读取字幕文件，编码问题", "summary": None}
            
            logger.info(f"成功读取字幕文件，文本长度: {len(subtitle_text)} 字符")
            
            # 处理字幕文本（移除时间戳和序号）
            cleaned_text = self._clean_subtitle_text(subtitle_text)
            
            if not cleaned_text:
                # 如果处理后为空，但原文本不为空，可能是格式问题，尝试直接使用原文本
                if len(subtitle_text.strip()) > 100:
                    logger.warning("处理后字幕文本为空，但原文本不为空，尝试使用原文本")
                    cleaned_text = subtitle_text.strip()
                else:
                    logger.error("处理后的字幕文本为空")
                    return {"success": False, "error": "字幕内容为空或格式无法识别", "summary": None}
            
            # 如果文本太长，截取前10000个字符
            if len(cleaned_text) > 10000:
                logger.warning(f"字幕文本过长 ({len(cleaned_text)} 字符)，截取前10000个字符")
                cleaned_text = cleaned_text[:10000]
            
            # 准备提示词
            prompt = self._prepare_prompt(cleaned_text)
            
            # 生成摘要
            summary = None
            
            # 首先尝试使用Ollama
            if self.use_ollama:
                summary = self._call_ollama(prompt)
            
            # 如果Ollama失败或不可用，使用在线API
            if summary is None:
                logger.info("Ollama生成摘要失败或不可用，尝试使用在线API")
                summary = self._call_online_api(prompt)
            
            if not summary:
                return {"success": False, "error": "生成摘要失败", "summary": None}
            
            return {"success": True, "error": None, "summary": summary}
            
        except Exception as e:
            logger.error(f"生成摘要时发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e), "summary": None}


# API处理函数
def generate_video_summary(video_id: str, subtitle_path: str) -> Dict[str, Any]:
    """
    为指定视频生成摘要的API函数
    
    Args:
        video_id: 视频ID
        subtitle_path: 字幕文件路径
        
    Returns:
        包含摘要和状态的字典
    """
    try:
        # 创建摘要生成器实例
        generator = SummaryGenerator()
        
        # 生成摘要
        result = generator.generate_summary(subtitle_path)
        
        if not result["success"]:
            logger.error(f"为视频 {video_id} 生成摘要失败: {result['error']}")
        else:
            logger.info(f"成功为视频 {video_id} 生成摘要")
        
        return result
        
    except Exception as e:
        logger.error(f"生成视频摘要时发生错误: {str(e)}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e), "summary": None}


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python summary_generator.py <字幕文件路径>")
        sys.exit(1)
    
    subtitle_path = sys.argv[1]
    result = generate_video_summary("test_video", subtitle_path)
    
    if result["success"]:
        print("\n生成的摘要:")
        print("-" * 50)
        print(result["summary"])
        print("-" * 50)
    else:
        print(f"生成摘要失败: {result['error']}")
