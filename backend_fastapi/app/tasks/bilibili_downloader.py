"""B站视频下载器 - 使用 bilibili-api-python"""

import os
import logging
import requests
import hashlib
import asyncio

logger = logging.getLogger(__name__)


def download_bilibili_video(bvid: str, output_path: str) -> dict:
    """
    同步下载B站视频（包装异步调用）
    
    Args:
        bvid: B站视频BV号
        output_path: 输出文件基础路径（不含扩展名）
        
    Returns:
        dict: 包含下载结果的字典
    """
    try:
        # 使用 bilibili_api 的同步 API
        from bilibili_api import sync, video
        
        # 同步获取视频信息
        v = video.Video(bvid=bvid)
        info = sync(v.get_info())
        
        title = info.get('title', 'unknown')
        cid = info.get('cid')
        
        logger.info(f"开始下载B站视频: {bvid}, 标题: {title}")
        
        # 同步获取下载URL
        url_data = sync(v.get_download_url(cid=cid))
        
        # 获取视频流URL
        dash_data = url_data.get('dash', {})
        video_streams = dash_data.get('video', [])
        audio_streams = dash_data.get('audio', [])
        
        if not video_streams:
            raise Exception('未找到视频流')
            
        # 选择最高质量的视频流
        video_stream = max(video_streams, key=lambda x: x.get('bandwidth', 0))
        video_url = video_stream.get('baseUrl', '')
        
        if not video_url:
            raise Exception('未获取到视频URL')
            
        # 下载视频
        logger.info(f"下载视频流: {video_stream.get('id')} - {video_stream.get('bandwidth')}bps")
        
        temp_video_path = output_path + '.temp_video.mp4'
        download_file(video_url, temp_video_path, '视频')
        
        # 下载音频（如果有）
        final_path = output_path + '.mp4'
        
        if audio_streams:
            audio_stream = audio_streams[0]
            audio_url = audio_stream.get('baseUrl', '')
            
            if audio_url:
                temp_audio_path = output_path + '.temp_audio.m4a'
                logger.info("下载音频流")
                download_file(audio_url, temp_audio_path, '音频')
                
                # 合并视频和音频（需要ffmpeg）
                if merge_video_audio(temp_video_path, temp_audio_path, final_path):
                    # 清理临时文件
                    try:
                        os.remove(temp_video_path)
                        os.remove(temp_audio_path)
                    except:
                        pass
                else:
                    # 合并失败，只使用视频
                    if os.path.exists(final_path):
                        os.remove(final_path)
                    os.rename(temp_video_path, final_path)
        else:
            # 没有音频流，直接使用视频
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(temp_video_path, final_path)
            
        # 计算MD5
        md5 = compute_md5(final_path)
        
        return {
            'success': True,
            'path': final_path,
            'title': title,
            'md5': md5,
            'filename': os.path.basename(final_path)
        }
        
    except Exception as e:
        logger.error(f"B站视频下载失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def download_file(url: str, output_path: str, file_type: str = '文件'):
    """同步下载文件"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com',
    }
    
    response = requests.get(url, headers=headers, stream=True)
    
    if response.status_code != 200:
        raise Exception(f"下载{file_type}失败: HTTP {response.status_code}")
        
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0 and downloaded % (1024 * 1024) == 0:
                    logger.info(f"下载{file_type}: {downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB")


def merge_video_audio(video_path: str, audio_path: str, output_path: str) -> bool:
    """使用ffmpeg合并视频和音频"""
    import subprocess
    
    try:
        cmd = [
            'ffmpeg', '-i', video_path, '-i', audio_path,
            '-c:v', 'copy', '-c:a', 'aac', '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info("视频音频合并成功")
            return True
        else:
            logger.warning(f"视频音频合并失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.warning(f"视频音频合并异常: {e}")
        return False


def compute_md5(file_path: str) -> str:
    """计算文件MD5"""
    digest = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()
