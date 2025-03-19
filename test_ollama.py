import requests
import json

# Ollama API配置
OLLAMA_BASE_URL = "http://localhost:11434/api"
OLLAMA_MODEL = "qwen2.5:7b"

# 简单的测试请求
try:
    print("正在测试Ollama API...")
    response = requests.post(
        f"{OLLAMA_BASE_URL}/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": "你好，请用一句话回答",
            "stream": False
        }
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print("响应内容:")
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    else:
        print(f"错误: {response.text}")
except Exception as e:
    print(f"发生异常: {str(e)}")
