import os

from volcenginesdkarkruntime import Ark

client = Ark(
    api_key="baba9884-7abc-4587-9225-a3886251deda",
)

# 初始化对话历史，添加系统提示要求展示思考过程
messages = [
    {
        "role": "system",
        "content": "在回答问题时，请先展示你的思考过程，然后再给出最终答案。分析问题时要逐步推理，思考全面。",
    }
]

print("=== DeepSeek-R1 AI助手交互式对话 ===")
print("(输入'exit'或'quit'退出对话)")
print("提示: 你可以在问题中明确要求AI'请展示思考过程'以获得更详细的推理")

while True:
    # 获取用户输入
    user_input = input("\n你: ")

    # 检查是否退出
    if user_input.lower() in ['exit', 'quit']:
        print("对话结束，再见！")
        break

    # 增强用户提示，如果用户没有明确要求思考过程
    if "思考" not in user_input and "推理" not in user_input and "分析" not in user_input:
        enhanced_input = user_input + "。请在回答前展示你的思考过程。"
    else:
        enhanced_input = user_input

    # 将用户输入添加到对话历史
    messages.append({"role": "user", "content": enhanced_input})

    # 创建流式对话请求，调整参数以促进思考过程展示
    print("\nAI: ", end="", flush=True)
    completion_stream = client.chat.completions.create(
        model="deepseek-r1-250120",
        messages=messages,
        stream=True,
        temperature=0.7,  # 适当提高温度以获得更详细的思考过程
        max_tokens=2000,  # 增加最大token数以获得更完整的思考过程
    )

    # 处理流式响应
    assistant_response = ""
    for chunk in completion_stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            assistant_response += content
            print(content, end="", flush=True)

    # 将助手回答添加到对话历史
    messages.append({"role": "assistant", "content": assistant_response})
