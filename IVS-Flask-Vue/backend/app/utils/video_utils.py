import os
import cv2
from urllib.parse import urlparse
from pytube import YouTube
from bilibili_api import video, Credential, sync
import requests
import re
import cv2
import requests
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import json
import subprocess

def is_valid_url(url):
    """检查URL是否有效"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def is_bilibili_url(url):
    """检查是否为哔哩哔哩视频链接"""
    return 'bilibili.com' in url.lower()

def is_youtube_url(url):
    """检查是否为YouTube视频链接"""
    return 'youtube.com' in url.lower() or 'youtu.be' in url.lower()

def download_bilibili_video(url, save_dir):
    """下载B站视频"""
    try:
        bv_id = extract_bv_from_url(url)
        output_path = os.path.join(save_dir, f"{bv_id}.mp4")
        return download_bilibili_video_by_bv(bv_id, output_path)
    except Exception as e:
        print(f"下载B站视频时出错: {str(e)}")
        raise e

def download_bilibili_video_by_bv(bv_id, output_path):
    """下载B站视频"""
    try:
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
            'Cookie': "buvid3=293C484D-D82D-73B8-D880-5AA943526C2B20905infoc"
        }

        # 获取视频信息
        api_url = f'https://api.bilibili.com/x/web-interface/view?bvid={bv_id}'
        response = requests.get(api_url, headers=headers)
        
        # 检查响应内容
        print(f"API响应状态码: {response.status_code}")
        print(f"API响应内容: {response.text}")
        
        if response.status_code != 200:
            raise Exception(f"API请求失败，状态码: {response.status_code}")
            
        data = response.json()
        if data['code'] != 0:
            raise Exception(f"获取视频信息失败: {data['message']}")
            
        title = data['data']['title']
        cid = data['data']['cid']
        print(f"获取到视频标题: {title}")
        print(f"获取到CID: {cid}")
        
        # 获取视频下载地址
        play_url = f'https://api.bilibili.com/x/player/playurl?bvid={bv_id}&cid={cid}&qn=80&fnval=16'
        response = requests.get(play_url, headers=headers)
        
        # 检查响应内容
        print(f"播放URL响应状态码: {response.status_code}")
        print(f"播放URL响应内容: {response.text}")
        
        if response.status_code != 200:
            raise Exception(f"获取播放URL失败，状态码: {response.status_code}")
            
        data = response.json()
        if data['code'] != 0:
            raise Exception(f"获取下载地址失败: {data['message']}")
            
        # 获取视频和音频流地址
        video_url = data['data']['dash']['video'][0]['baseUrl']
        audio_url = data['data']['dash']['audio'][0]['baseUrl']
        
        print("正在获取下载地址...")
        print(f"视频流地址: {video_url}")
        print(f"音频流地址: {audio_url}")
        
        # 下载视频流
        video_temp = os.path.join(os.path.dirname(output_path), 'temp_video.m4s')
        print(f"正在下载视频流到: {video_temp}")
        response = requests.get(video_url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"下载视频流失败，状态码: {response.status_code}")
            
        with open(video_temp, 'wb') as f:
            f.write(response.content)
            
        # 下载音频流
        audio_temp = os.path.join(os.path.dirname(output_path), 'temp_audio.m4s')
        print(f"正在下载音频流到: {audio_temp}")
        response = requests.get(audio_url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"下载音频流失败，状态码: {response.status_code}")
            
        with open(audio_temp, 'wb') as f:
            f.write(response.content)
            
        # 使用ffmpeg合并视频和音频
        print("正在合并视频和音频...")
        command = [
            'ffmpeg', '-i', video_temp,
            '-i', audio_temp,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            output_path,
            '-y'
        ]
        subprocess.run(command, check=True)
        
        # 清理临时文件
        if os.path.exists(video_temp):
            os.remove(video_temp)
        if os.path.exists(audio_temp):
            os.remove(audio_temp)
        
        print(f"视频下载成功: {title}")
        return output_path, title
        
    except Exception as e:
        print(f"下载视频时出错: {str(e)}")
        # 清理临时文件
        video_temp = os.path.join(os.path.dirname(output_path), 'temp_video.m4s')
        audio_temp = os.path.join(os.path.dirname(output_path), 'temp_audio.m4s')
        if os.path.exists(video_temp):
            os.remove(video_temp)
        if os.path.exists(audio_temp):
            os.remove(audio_temp)
        raise

def extract_bv_from_url(url):
    """从URL中提取BV号"""
    try:
        if 'BV' in url:
            bv_start = url.index('BV')
            bv_id = url[bv_start:bv_start+12]
            print(f"提取到的BV号: {bv_id}")
            return bv_id
    except Exception as e:
        print(f"提取BV号时出错: {str(e)}")
        raise
    raise Exception("未找到BV号")

def get_video_info(video_path):
    """获取视频信息"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("无法打开视频文件")
            
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            'width': width,
            'height': height,
            'fps': fps,
            'frame_count': frame_count,
            'duration': duration
        }
        
    except Exception as e:
        print(f"获取视频信息时出错: {str(e)}")
        raise

def download_youtube_video(url, save_path):
    """下载YouTube视频"""
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if not stream:
            return None
            
        # 下载视频
        stream.download(filename=save_path)
        
        return {
            'title': yt.title,
            'path': save_path
        }
    except Exception as e:
        print(f"下载YouTube视频时出错: {str(e)}")
        return None

def ensure_upload_folder(app):
    """确保上传文件夹存在"""
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder
