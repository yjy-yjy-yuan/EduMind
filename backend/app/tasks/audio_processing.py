import os
import subprocess
from .. import celery, db
from ..models.video import Video
from ..models.subtitle import Subtitle
import whisper
import json

def extract_audio(video_path, output_path):
    """从视频中提取音频"""
    try:
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # 不处理视频
            '-acodec', 'pcm_s16le',  # 音频编码为16位PCM
            '-ar', '16000',  # 采样率16kHz
            '-ac', '1',  # 单声道
            '-y',  # 覆盖已存在的文件
            output_path
        ]
        subprocess.run(command, check=True)
        return True
    except Exception as e:
        print(f"提取音频时出错: {str(e)}")
        return False

def extract_subtitles(video_path):
    """从视频中提取字幕"""
    try:
        # 尝试提取内嵌字幕
        command = [
            'ffmpeg',
            '-i', video_path,
            '-map', '0:s:0',  # 选择第一个字幕流
            '-f', 'srt',
            '-'  # 输出到stdout
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout:
            return result.stdout
        return None
    except Exception as e:
        print(f"提取字幕时出错: {str(e)}")
        return None

def parse_srt(srt_content):
    """解析SRT格式字幕"""
    def time_to_seconds(time_str):
        """将SRT时间格式转换为秒"""
        hours, minutes, seconds = time_str.replace(',', '.').split(':')
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    
    subtitles = []
    current = {}
    
    for line in srt_content.strip().split('\n'):
        line = line.strip()
        
        if not line:  # 空行表示一个字幕块的结束
            if current:
                subtitles.append(current)
                current = {}
        elif current.get('index') is None:
            current['index'] = int(line)
        elif current.get('time') is None:
            start, end = line.split(' --> ')
            current['start_time'] = time_to_seconds(start)
            current['end_time'] = time_to_seconds(end)
        elif current.get('text') is None:
            current['text'] = line
        else:
            current['text'] += '\n' + line
            
    if current:  # 添加最后一个字幕
        subtitles.append(current)
        
    return subtitles

@celery.task(bind=True)
def process_audio_and_subtitles(self, video_id):
    """处理视频的音频和字幕"""
    try:
        # 获取视频记录
        video = Video.query.get(video_id)
        if not video:
            print(f"未找到ID为{video_id}的视频")
            return {
                'status': 'error',
                'message': f'未找到ID为{video_id}的视频'
            }
            
        print(f"开始处理视频音频和字幕: {video.title}")
        
        # 获取音频目录的绝对路径
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        audio_dir = os.path.join(base_dir, 'audio')
        
        # 确保音频目录存在
        os.makedirs(audio_dir, exist_ok=True)
        
        # 提取音频
        audio_filename = f"{video.title}_{video.id}.wav"
        audio_path = os.path.join(audio_dir, audio_filename)
        
        if extract_audio(video.processed_filepath or video.filepath, audio_path):
            print("音频提取成功")
            
            # 尝试提取内嵌字幕
            srt_content = extract_subtitles(video.processed_filepath or video.filepath)
            if srt_content:
                print("成功提取内嵌字幕")
                subtitles = parse_srt(srt_content)
                for sub in subtitles:
                    subtitle = Subtitle(
                        video_id=video.id,
                        start_time=sub['start_time'],
                        end_time=sub['end_time'],
                        text=sub['text'],
                        source='extract',
                        language='zh'  # 假设提取的字幕是中文
                    )
                    db.session.add(subtitle)
                db.session.commit()
            
            # 使用Whisper进行语音识别
            print("开始语音识别...")
            model = whisper.load_model("medium")  # 使用medium模型，可以根据需要调整
            result = model.transcribe(audio_path, language="zh")
            
            # 保存识别结果
            for segment in result['segments']:
                subtitle = Subtitle(
                    video_id=video.id,
                    start_time=segment['start'],
                    end_time=segment['end'],
                    text=segment['text'],
                    source='asr',
                    language='zh'
                )
                db.session.add(subtitle)
            
            db.session.commit()
            print("语音识别完成")
            
            # 删除临时音频文件
            os.remove(audio_path)
            
            return {
                'status': 'success',
                'message': '音频和字幕处理完成'
            }
        else:
            raise Exception("音频提取失败")
            
    except Exception as e:
        print(f"处理音频和字幕时出错: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }
