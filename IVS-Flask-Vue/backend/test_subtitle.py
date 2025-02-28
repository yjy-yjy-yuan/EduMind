import requests
import json
import time

def test_subtitle_generation():
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
            return
            
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
            return
            
        # 获取任务ID
        task_id = response.json().get('task_id')
        
        print("\n=== 第3步：等待字幕生成完成 ===")
        max_retries = 60  # 最多等待60秒
        retry_count = 0
        
        while retry_count < max_retries:
            # 查询字幕状态
            response = requests.get(f'{base_url}/api/videos/{video_id}/subtitles')
            subtitle_data = response.json()
            
            if response.status_code == 200 and subtitle_data.get('subtitles'):
                print("字幕生成成功！")
                print(f"生成的字幕数量: {len(subtitle_data['subtitles'])}")
                print("\n=== 字幕内容 ===")
                for subtitle in subtitle_data['subtitles']:
                    start_time = round(subtitle['start_time'])
                    end_time = round(subtitle['end_time'])
                    text = subtitle['text']
                    print(f"[{start_time:02d}s -> {end_time:02d}s] {text}")
                return
                
            print("字幕生成中，等待1秒...")
            time.sleep(1)
            retry_count += 1
            
        print("等待超时，字幕生成可能失败")
        
    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {str(e)}")
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")

if __name__ == '__main__':
    test_subtitle_generation()
