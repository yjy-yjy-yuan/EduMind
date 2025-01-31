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
        # 确保使用正确的路径分隔符并转换为绝对路径
        download_folder = os.path.abspath(download_folder)
        os.makedirs(download_folder, exist_ok=True)
        
        # 通用的下载配置
        common_opts = {
            'format': 'bestvideo*+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: progress_hook(d)],
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
        }
        
        # 通用User-Agent
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        # 区分不同平台的下载配置
        if "bilibili.com" in video_link or "b23.tv" in video_link or video_link.startswith('BV'):
            # Bilibili 特定配置
            ydl_opts = {
                **common_opts,
                'http_headers': {
                    'Referer': 'https://www.bilibili.com',
                    'User-Agent': user_agent
                }
            }
            
            # 处理 Bilibili 短链接
            if "b23.tv" in video_link:
                import requests
                headers = {'User-Agent': user_agent}
                response = requests.head(video_link, headers=headers, allow_redirects=True)
                video_link = response.url
                
            # 处理 BV 号格式
            if video_link.startswith('BV'):
                video_link = f"https://www.bilibili.com/video/{video_link}"
        else:
            # YouTube 等其他平台的配置
            ydl_opts = {
                **common_opts,
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # 优先选择mp4格式
                'http_headers': {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate',
                },
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'no_warnings': True,
                'extractor_args': {'youtube': {
                    'player_client': ['android', 'web'],  # 尝试多个客户端
                    'player_skip': ['webpage', 'config', 'js'],  # 跳过可能导致问题的检查
                }},
                'socket_timeout': 30,  # 增加超时时间
                'retries': 10,  # 增加重试次数
                'file_access_retries': 10,
                'fragment_retries': 10,
                'skip_unavailable_fragments': True,
                'overwrites': True,
            }
            
            # 如果是YouTube链接，尝试规范化URL
            if 'youtube.com' in video_link or 'youtu.be' in video_link:
                try:
                    # 处理短链接
                    if 'youtu.be' in video_link:
                        video_id = video_link.split('/')[-1].split('?')[0]
                        video_link = f'https://www.youtube.com/watch?v={video_id}'
                    # 清理URL参数
                    if '&' in video_link:
                        video_link = video_link.split('&')[0]
                except Exception:
                    pass  # 如果URL处理失败，使用原始URL
        
        # 下载视频
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_link, download=True)
            video_title = info['title']
            safe_title = get_safe_filename(video_title)
            video_path = os.path.join(download_folder, f"{safe_title}.mp4")
            
            # 确保文件存在
            if not os.path.exists(video_path):
                # 尝试查找实际下载的文件
                potential_files = [f for f in os.listdir(download_folder) if f.startswith(safe_title)]
                if potential_files:
                    video_path = os.path.join(download_folder, potential_files[0])
            
            if os.path.exists(video_path):
                return video_path, safe_title
            else:
                raise FileNotFoundError(f"无法找到下载的视频文件: {video_path}")
                
    except Exception as e:
        st.error(f"下载视频时出错: {str(e)}")
        return None, None
