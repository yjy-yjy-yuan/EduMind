# 功能：测试字幕导出和编辑功能，包含之前的上传视频、处理视频、生成字幕、导出字幕
import requests
import json
import time
import os

def upload_video_and_generate_subtitles():
    """上传视频并生成字幕"""
    base_url = 'http://localhost:5000'
    
    print("=== 第1步：上传视频 ===")
    print("正在发送上传请求...")
    
    # 准备请求数据
    data = {
        'language': 'zh',  # 使用中文
        'whisper_model': 'base',  # 使用base模型
        'video_url': 'https://www.bilibili.com/video/BV1goFQedEba'
    }
    
    print(f"请求URL: {base_url}/api/videos/upload")
    print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    # 发送上传请求
    try:
        response = requests.post(
            f'{base_url}/api/videos/upload',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\n状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code != 200:
            print("视频上传失败，终止测试")
            return None
            
        # 获取上传的视频ID
        video_id = response.json()['video']['id']
        
        print("\n=== 第2步：生成字幕 ===")
        print("正在发送字幕生成请求...")
        
        # 准备字幕生成请求数据
        subtitle_data = {
            'language': 'zh',  # 确保使用正确的语言代码
            'whisper_model': 'base'  # 使用base模型
        }
        
        # 发送字幕生成请求
        response = requests.post(
            f'{base_url}/api/videos/{video_id}/subtitles/generate',
            json=subtitle_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\n状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code != 200:
            print("字幕生成请求失败，终止测试")
            return None
            
        print("\n=== 第3步：等待字幕生成完成 ===")
        max_retries = 60  # 最多等待60秒
        retry_count = 0
        
        while retry_count < max_retries:
            # 查询字幕状态
            response = requests.get(f'{base_url}/api/videos/{video_id}/subtitles')
            if response.status_code == 200:
                subtitle_data = response.json()
                if subtitle_data.get('subtitles'):
                    print("字幕生成成功！")
                    print(f"生成的字幕数量: {len(subtitle_data['subtitles'])}")
                    return video_id
            
            print("字幕生成中，等待1秒...")
            time.sleep(1)
            retry_count += 1
            
        print("等待超时，字幕生成可能失败")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {str(e)}")
        return None
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        return None

def test_subtitle_export():
    """测试字幕导出和编辑功能"""
    base_url = 'http://localhost:5000'
    
    # 先上传视频并生成字幕
    print("=== 准备测试数据 ===")
    video_id = upload_video_and_generate_subtitles()
    if not video_id:
        print("准备测试数据失败")
        return
    
    print("\n=== 第4步：测试字幕导出功能 ===")
    # 确保captions目录存在
    captions_dir = 'captions'
    os.makedirs(captions_dir, exist_ok=True)
    
    # 测试不同格式的导出
    formats = ['srt', 'vtt', 'txt']
    for format_type in formats:
        print(f"\n正在测试导出 {format_type} 格式...")
        response = requests.get(
            f'{base_url}/api/videos/{video_id}/subtitles/export',
            params={'format': format_type}
        )
        
        if response.status_code == 200:
            # 保存文件到captions目录
            filename = os.path.join(captions_dir, f"test_subtitle.{format_type}")
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"成功导出 {format_type} 格式字幕到文件: {filename}")
            
            # 显示文件内容
            with open(filename, 'r', encoding='utf-8') as f:
                print("\n文件内容预览:")
                print(f.read()[:500])  # 只显示前500个字符
        else:
            print(f"导出 {format_type} 格式失败:")
            print(response.json())
    
    print("\n=== 第5步：测试字幕编辑功能 ===")
    # 获取所有字幕
    response = requests.get(f'{base_url}/api/videos/{video_id}/subtitles')
    if response.status_code != 200:
        print("获取字幕失败")
        return
        
    subtitles = response.json().get('subtitles', [])
    if not subtitles:
        print("没有找到字幕")
        return
        
    # 测试编辑第一个字幕
    first_subtitle = subtitles[0]
    subtitle_id = first_subtitle['id']
    original_text = first_subtitle['text']
    
    edit_data = {
        'text': f'[已编辑] {original_text}',
        'editor': 'test_user'
    }
    
    print("\n正在编辑字幕...")
    print(f"原始文本: {original_text}")
    print(f"编辑后文本: {edit_data['text']}")
    
    response = requests.put(
        f'{base_url}/api/videos/{video_id}/subtitles/{subtitle_id}',
        json=edit_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        print("字幕编辑成功！")
        print("编辑后的字幕:")
        print(json.dumps(response.json()['subtitle'], indent=2, ensure_ascii=False))
    else:
        print("字幕编辑失败:")
        print(response.json())
    
    print("\n=== 第6步：测试字幕合并功能 ===")
    print("正在合并字幕...")
    response = requests.post(
        f'{base_url}/api/videos/{video_id}/subtitles/merge',
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        print("字幕合并成功！")
        merged_subtitles = response.json()['subtitles']
        print(f"合并前字幕数量: {len(subtitles)}")
        print(f"合并后字幕数量: {len(merged_subtitles)}")
        
        print("\n合并后的字幕预览:")
        for subtitle in merged_subtitles[:3]:  # 只显示前3个字幕
            start_time = round(subtitle['start_time'])
            end_time = round(subtitle['end_time'])
            text = subtitle['text']
            print(f"[{start_time:02d}s -> {end_time:02d}s] {text}")
    else:
        print("字幕合并失败:")
        print(response.json())

if __name__ == '__main__':
    test_subtitle_export()
