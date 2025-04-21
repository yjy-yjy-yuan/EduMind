import json
import os

def check_subtitle_file(file_path):
    """检查字幕文件格式
    
    Args:
        file_path: 字幕文件路径
    """
    try:
        print(f"正在检查字幕文件: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"错误: 文件不存在")
            return
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"文件大小: {len(content)} 字节")
            print(f"文件前100个字符: {content[:100]}...")
        
        # 尝试解析JSON
        try:
            data = json.loads(content)
            print(f"JSON解析成功")
            print(f"数据类型: {type(data).__name__}")
            
            if isinstance(data, dict):
                print(f"字典键: {list(data.keys())}")
                
                # 检查是否有字幕数据
                if 'subtitles' in data and isinstance(data['subtitles'], list):
                    print(f"找到字幕数组，包含 {len(data['subtitles'])} 条字幕")
                    if len(data['subtitles']) > 0:
                        print(f"第一条字幕: {data['subtitles'][0]}")
            elif isinstance(data, list):
                print(f"数组长度: {len(data)}")
                if len(data) > 0:
                    print(f"第一个元素: {data[0]}")
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {str(e)}")
    
    except Exception as e:
        print(f"检查字幕文件时出错: {str(e)}")

if __name__ == "__main__":
    # 检查字幕文件
    subtitle_file = os.path.join('backend', 'uploads', 'subtitles', 'local-【中文励志演讲】每个人都是自己的砥柱.json')
    check_subtitle_file(subtitle_file)
