"""
视频标签生成服务
使用ollama模型或在线API处理视频摘要，生成相关标签
"""
import os
import json
import requests
import logging
import traceback
import re
from typing import Dict, Any, Optional, List

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ollama API配置
OLLAMA_BASE_URL = "http://localhost:11434/api"
OLLAMA_MODEL = "deepseek-r1:8b"  # 使用deepseek-r1:8b模型

# 在线API配置
OPENAI_API_KEY = "sk-59a6a7690bfb42cd887365795e114002"
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

class TagGenerator:
    """视频标签生成器，使用ollama模型或在线API处理摘要生成标签"""
    
    def __init__(self):
        """初始化标签生成器"""
        # 检查Ollama服务是否可用
        self.use_ollama = check_ollama_service()
        if self.use_ollama:
            logger.info(f"将使用本地Ollama模型: {OLLAMA_MODEL}")
        else:
            logger.info("Ollama服务不可用，将使用在线API")
    
    def _prepare_prompt(self, summary: str) -> str:
        """
        准备提示词
        
        Args:
            summary: 视频摘要文本
            
        Returns:
            格式化后的提示词
        """
        prompt = f"""你是一个专业的教育视频内容分析助手。请根据以下视频摘要内容，提供2-3个最能代表视频主题的标签。

视频摘要:
```
{summary}
```

请生成2-3个标签，要求：
1. 每个标签应当简洁明了，通常为2-5个词
2. 标签应当反映视频的学科领域、主题或关键概念
3. 标签应当从大类到小类排序，例如先是"数学"这样的大类，再是"微积分"这样的具体主题
4. 不要使用过于宽泛的标签，如"教育"、"学习"等

请直接以JSON数组格式输出标签，例如：["数学", "微积分", "导数", "应用"]
不要包含任何其他解释或前缀。
"""
        return prompt
    
    def _call_ollama(self, prompt: str) -> Optional[List[str]]:
        """
        调用ollama API生成标签
        
        Args:
            prompt: 提示词
            
        Returns:
            生成的标签列表，如果失败则返回None
        """
        try:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 200
                }
            }
            
            logger.info(f"调用ollama API生成标签，模型: {OLLAMA_MODEL}")
            response = requests.post(f"{OLLAMA_BASE_URL}/generate", json=payload, timeout=60)
            
            if response.status_code != 200:
                logger.error(f"ollama API调用失败: {response.status_code}, {response.text}")
                return None
                
            result = response.json()
            tags_text = result.get("response", "").strip()
            logger.info(f"Ollama生成的标签文本: {tags_text}")
            
            # 解析JSON格式的标签
            try:
                # 尝试直接解析
                tags = json.loads(tags_text)
                if isinstance(tags, list):
                    return tags
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试提取JSON数组部分
                match = re.search(r'\[.*?\]', tags_text, re.DOTALL)
                if match:
                    try:
                        tags = json.loads(match.group(0))
                        if isinstance(tags, list):
                            return tags
                    except json.JSONDecodeError:
                        pass
            
            # 如果上述方法都失败，尝试简单的文本分割
            if ',' in tags_text:
                # 移除可能的方括号
                clean_text = tags_text.replace('[', '').replace(']', '')
                # 按逗号分割
                tags = [tag.strip().strip('"\'') for tag in clean_text.split(',')]
                return tags
                
            logger.error(f"无法解析生成的标签文本: {tags_text}")
            return None
            
        except Exception as e:
            logger.error(f"调用ollama API时发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def _call_online_api(self, prompt: str) -> Optional[List[str]]:
        """
        调用在线API生成标签
        
        Args:
            prompt: 提示词
            
        Returns:
            生成的标签列表，如果失败则返回None
        """
        try:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "你是一个专业的教育视频内容分析助手，负责生成视频标签。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 200
            }
            
            logger.info("调用在线API生成标签")
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
            tags_text = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logger.info(f"在线API生成的标签文本: {tags_text}")
            
            # 解析JSON格式的标签
            try:
                # 尝试直接解析
                tags = json.loads(tags_text)
                if isinstance(tags, list):
                    return tags
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试提取JSON数组部分
                match = re.search(r'\[.*?\]', tags_text, re.DOTALL)
                if match:
                    try:
                        tags = json.loads(match.group(0))
                        if isinstance(tags, list):
                            return tags
                    except json.JSONDecodeError:
                        pass
            
            # 如果上述方法都失败，尝试简单的文本分割
            if ',' in tags_text:
                # 移除可能的方括号
                clean_text = tags_text.replace('[', '').replace(']', '')
                # 按逗号分割
                tags = [tag.strip().strip('"\'') for tag in clean_text.split(',')]
                return tags
                
            logger.error(f"无法解析生成的标签文本: {tags_text}")
            return None
            
        except Exception as e:
            logger.error(f"调用在线API时发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def generate_tags(self, summary: str) -> Dict[str, Any]:
        """
        从视频摘要生成标签
        
        Args:
            summary: 视频摘要文本
            
        Returns:
            包含标签和状态的字典
        """
        try:
            if not summary or len(summary.strip()) < 10:
                logger.error("摘要内容为空或太短")
                return {"success": False, "error": "摘要内容为空或太短", "tags": None}
            
            # 准备提示词
            prompt = self._prepare_prompt(summary)
            
            # 生成标签
            tags = None
            
            # 首先尝试使用Ollama
            if self.use_ollama:
                tags = self._call_ollama(prompt)
            
            # 如果Ollama失败或不可用，使用在线API
            if tags is None:
                logger.info("Ollama生成标签失败或不可用，尝试使用在线API")
                tags = self._call_online_api(prompt)
            
            if not tags:
                return {"success": False, "error": "生成标签失败", "tags": None}
            
            # 限制标签数量为5个
            if len(tags) > 5:
                tags = tags[:5]
            
            return {"success": True, "error": None, "tags": tags}
            
        except Exception as e:
            logger.error(f"生成标签时发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e), "tags": None}


# API处理函数
def generate_video_tags(video_id: str, summary: str) -> Dict[str, Any]:
    """
    为指定视频生成标签的API函数
    
    Args:
        video_id: 视频ID
        summary: 视频摘要
        
    Returns:
        包含标签和状态的字典
    """
    try:
        # 创建标签生成器实例
        generator = TagGenerator()
        
        # 生成标签
        result = generator.generate_tags(summary)
        
        if not result["success"]:
            logger.error(f"为视频 {video_id} 生成标签失败: {result['error']}")
        else:
            logger.info(f"成功为视频 {video_id} 生成标签: {result['tags']}")
        
        return result
        
    except Exception as e:
        logger.error(f"生成视频标签时发生错误: {str(e)}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e), "tags": None}


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python tag_generator.py <摘要文本>")
        sys.exit(1)
    
    summary = sys.argv[1]
    result = generate_video_tags("test_video", summary)
    
    if result["success"]:
        print("\n生成的标签:")
        print("-" * 50)
        print(result["tags"])
        print("-" * 50)
    else:
        print(f"生成标签失败: {result['error']}")
