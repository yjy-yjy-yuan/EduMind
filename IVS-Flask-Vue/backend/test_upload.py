# 功能：测试B站视频上传

import requests
import json

def test_upload_video():
    # 测试B站视频上传
    url = 'http://localhost:5000/api/videos/upload'
    
    # 准备表单数据
    data = {
        'language': 'zh',  # 视频语言
        'whisper_model': 'base',  # whisper模型
        'video_url': 'https://www.bilibili.com/video/BV1goFQedEba'  # B站视频链接
    }
    
    try:
        print("正在发送上传请求...")
        print(f"请求URL: {url}")
        print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, data=data)
        print(f"\n状态码: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"响应内容: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
            
            if response.status_code == 200:
                print("\n视频上传成功！")
                print(f"视频信息: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
                return response_json  # 直接返回完整的响应JSON
            else:
                print("\n上传失败: ", end="")
                print(json.dumps(response_json, ensure_ascii=False, indent=2))
                return None
        except json.JSONDecodeError:
            print("响应内容: ", response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        print("错误：无法连接到服务器，请确保Flask服务器正在运行")
        return None
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        print("\n详细错误信息:")
        print(traceback.format_exc())
        return None

if __name__ == '__main__':
    test_upload_video()
