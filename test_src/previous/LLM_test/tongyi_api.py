import os
from openai import OpenAI

def stream_chat():
    client = OpenAI(
        api_key="sk-178e130a121445659860893fdfae1e7d",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    # 创建一个对话历史列表，使用简单的系统提示词
    system_prompt = '''你是一个教育助手，请始终使用中文回答问题。'''
    
    print("欢迎使用通义千问聊天机器人（深度思考模式）！输入 'quit' 退出对话。")
    
    messages = [
        {'role': 'system', 'content': system_prompt}
    ]
    
    while True:
        # 获取用户输入
        user_input = input("\n用户: ")
        
        # 处理特殊命令
        if user_input.lower() == 'quit':
            print("再见！")
            break
        
        # 在用户输入前添加"深度思考"指令
        modified_input = f"深度思考\n{user_input}"
        
        # 将修改后的用户输入添加到对话历史
        messages.append({'role': 'user', 'content': modified_input})
        
        try:
            # 创建流式响应
            stream = client.chat.completions.create(
                model="deepseek-r1",
                messages=messages,
                stream=True  # 启用流式输出
            )
            
            print("\n助手: ", end="", flush=True)
            assistant_message = ""
            
            # 逐字输出响应
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    assistant_message += content
            
            # 将助手的完整回复添加到对话历史
            messages.append({'role': 'assistant', 'content': assistant_message})
            
            # 分析回答，尝试识别思考过程和最终答案
            print("\n\n===== 思考过程和答案分析 =====")
            
            # 尝试识别思考过程和最终答案的分隔点
            import re
            
            # 查找明显的分隔点，通常是一个空行后跟着一个不以思考过程特征开头的段落
            paragraphs = assistant_message.split('\n\n')
            if len(paragraphs) >= 2:
                # 假设第一段是思考过程，最后一段是最终答案
                thinking_process = '\n\n'.join(paragraphs[:-1])
                final_answer = paragraphs[-1]
                
                print(f"\n思考过程:\n{thinking_process}")
                print(f"\n最终答案:\n{final_answer}")
            else:
                print("\n未能识别思考过程和最终答案的分隔")
                print(f"\n完整回答:\n{assistant_message}")
            
            print("===== 分析结束 =====\n")
            
        except Exception as e:
            print(f"\n错误信息：{e}")
            print("请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code")

if __name__ == "__main__":
    stream_chat()
