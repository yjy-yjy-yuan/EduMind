# 下载视频：目前支持YouTube、bilibili

import os
import re
import yt_dlp
import streamlit as st

#清理文件名，移除特殊字符
def sanitize_filename(filename):
    cleaned = re.sub(r'[<>:"/\\|?*\u0000-\u001F\u007F-\u009F]', '_', filename)
    cleaned = cleaned.strip('. ')
    return cleaned

# 生成安全的文件名
def get_safe_filename(original_name):
    name, ext = os.path.splitext(original_name)
    safe_name = sanitize_filename(name)
    return f"{safe_name}{ext}"

# 显示下载进度的回调函数
def progress_hook(d):
    if d['status'] == 'downloading':
        try:
            progress = float(d.get('_percent_str', '0%').replace('%', '')) / 100
            status_msg = (f"正在下载: {d.get('_percent_str', '0%')} | "
                        f"速度: {d.get('_speed_str', '0 B/s')} | "
                        f"剩余时间: {d.get('_eta_str', '未知')}")
            
            st.progress(progress)
            st.text(status_msg)
        except Exception:
            pass   
        
# 使用 yt-dlp 下载视频并返回可播放的文件路径(主函数调用)
def download_and_play_video(video_link, download_folder="../IVS/downloads"):
    try:
        os.makedirs(download_folder, exist_ok=True)
        
        # 区分不同平台的下载配置
        if "bilibili.com" in video_link or "b23.tv" in video_link or video_link.startswith('BV'):
            # Bilibili 视频的下载配置
            ydl_opts = {
                'format': 'bestvideo*+bestaudio/best',  # 下载最佳视频和音频质量
                'merge_output_format': 'mp4',  # 强制合并为mp4
                'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
                'progress_hooks': [lambda d: progress_hook(d)],
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                'http_headers': {
                    'Referer': 'https://www.bilibili.com',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            }
            
            # 处理 Bilibili 短链接
            if "b23.tv" in video_link:
                import requests
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.head(video_link, headers=headers, allow_redirects=True)
                video_link = response.url
                
            # 处理 BV 号格式
            if video_link.startswith('BV'):
                video_link = f"https://www.bilibili.com/video/{video_link}"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_link, download=True)
                video_title = info['title']
                safe_title = get_safe_filename(video_title)
                video_path = os.path.join(download_folder, f"{safe_title}.mp4")
                
                return video_path, safe_title
                
        else:
            # YouTube 等其他平台的默认配置
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
                'progress_hooks': [lambda d: progress_hook(d)],
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4'
                }]
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_link, download=True)
            video_title = info['title']
            safe_title = get_safe_filename(video_title)
            video_path = os.path.join(download_folder, f"{safe_title}.mp4")
            
            return video_path, safe_title
            
    except yt_dlp.utils.DownloadError as e:
        error_str = str(e)
        if "Requested format is not available" in error_str:
            st.error(f"无法获取视频格式: {error_str}")
        else:
            st.error(f"视频下载失败: {error_str}")
        return None, None
    except Exception as e:
        st.error(f"发生未知错误: {str(e)}")
        return None, None
