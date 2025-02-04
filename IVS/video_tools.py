"""
1、实现功能：
    视频处理工具集合
    视频信息提取
    视频下载功能
    音频分析和处理
    音频转录功能
2、主要技术：
    使用 FFmpeg 进行视频处理
    集成 Whisper 模型进行语音识别
    使用 you-get 进行视频下载
    支持音频段落分析
    实现了静音检测算法
    支持 GPU 加速处理
"""

import os
import subprocess
import whisper
from opencc import OpenCC
import torch
from typing import Dict, List, Optional
import json

class VideoTools:
    # 初始化VideoTools类
    def __init__(self, whisper_model="base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading Whisper model: {whisper_model} on {self.device}")
        
        self.whisper_model = whisper.load_model(whisper_model).to(self.device)
        self.cc = OpenCC('t2s')
        
        self.transcribe_options = {
            "task": "transcribe",
            "beam_size": 5,
            "best_of": 5,
            "fp16": torch.cuda.is_available(),
            "condition_on_previous_text": True,
            "verbose": False
        }

    # 从视频中提取音频
    def get_video_info(self, video_path: str) -> Dict:
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            return json.loads(result.stdout)
        except Exception as e:
            print(f"Error getting video info: {e}")
            return {}

    # 下载视频
    def download_video(
        self, 
        url: str, 
        download_dir: str, 
        resolution: str = 'best'
    ) -> Optional[str]:
        """下载视频"""
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        
        os.chdir(download_dir)
        try:
            subprocess.run(
                ['you-get', '-o', download_dir, '--format', resolution, url],
                check=True
            )
            
            for file in os.listdir(download_dir):
                if file.endswith('.mp4'):
                    return os.path.join(download_dir, file)
            return None
        except subprocess.CalledProcessError as e:
            print(f"Error downloading video: {e}")
            return None

    # 检测音频中的静音片段
    def detect_silence(
        self, 
        audio_path: str, 
        noise_threshold: float = -30,
        duration: float = 0.5
    ) -> List[Dict]:
        try:
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-af', f'silencedetect=n={noise_threshold}dB:d={duration}',
                '-f', 'null', '-'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            silence_periods = []
            current_period = None
            
            for line in result.stderr.split('\n'):
                if 'silence_start' in line:
                    time = float(line.split('silence_start: ')[1])
                    current_period = {'start': time}
                elif 'silence_end' in line and current_period:
                    time = float(line.split('silence_end: ')[1].split(' ')[0])
                    current_period['end'] = time
                    current_period['duration'] = time - current_period['start']
                    silence_periods.append(current_period)
                    current_period = None
            
            return silence_periods
        except Exception as e:
            print(f"Error detecting silence: {e}")
            return []

    # 分析音频片段    
    def analyze_audio_segments(
        self, 
        video_path: str,
        min_segment_length: float = 0.5
    ) -> List[Dict]:
        try:
            audio_path = self.extract_audio(video_path)
            if not audio_path:
                return []
            
            silence_periods = self.detect_silence(audio_path)
            os.remove(audio_path)  # 清理临时音频文件
            
            # 分析非静音片段
            segments = []
            last_end = 0
            
            for silence in silence_periods:
                if silence['start'] - last_end >= min_segment_length:
                    segments.append({
                        'start': last_end,
                        'end': silence['start'],
                        'duration': silence['start'] - last_end
                    })
                last_end = silence['end']
            
            return segments
        except Exception as e:
            print(f"Error analyzing audio segments: {e}")
            return []
    
    # 转录音频
    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> Optional[str]:
        try:
            if output_path is None:
                output_path = f"{os.path.splitext(video_path)[0]}_audio.wav"
                
            # 先获取视频信息
            probe_cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-i',
                video_path
            ]
            
            # 使用特定的编码运行命令
            process = subprocess.Popen(
                probe_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='ignore'
            )
            stdout, _ = process.communicate()
            
            try:
                video_info = json.loads(stdout)
            except json.JSONDecodeError:
                print("Failed to parse video info")
                video_info = {"streams": []}
            
            # 检查是否有音频流
            has_audio = False
            for stream in video_info.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    has_audio = True
                    break
            
            if not has_audio:
                print("No audio stream found in the video")
                # 创建一个空的音频文件
                empty_audio_cmd = [
                    'ffmpeg',
                    '-f', 'lavfi',
                    '-i', 'anullsrc=r=16000:cl=mono',
                    '-t', '0.1',  # 生成0.1秒的静音
                    '-acodec', 'pcm_s16le',
                    '-ar', '16000',
                    '-ac', '1',
                    '-y',
                    output_path
                ]
                
                process = subprocess.Popen(
                    empty_audio_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding='utf-8',
                    errors='ignore'
                )
                _, stderr = process.communicate()
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return output_path
                else:
                    print(f"Failed to create empty audio: {stderr}")
                    return None
            
            # 如果有音频流，则提取音频
            command = [
                'ffmpeg',
                '-i', video_path,
                '-vn',
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y',
                output_path
            ]
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='ignore'
            )
            _, stderr = process.communicate()
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
            else:
                print(f"Audio extraction failed: {stderr}")
                return None
                
        except Exception as e:
            print(f"Error extracting audio: {e}")
            return None

    # 验证并修正时间戳
    def validate_timestamps(self, segments: List[Dict]) -> List[Dict]:
        if not segments:
            return []
            
        corrected_segments = []
        last_end = 0
        last_text = ""
        min_duration = 0.3  # Minimum segment duration in seconds
        
        for segment in segments:
            # Skip segments that are too similar to the previous one
            if segment['text'].strip() == last_text:
                continue
                
            # Ensure start time is not earlier than last end time
            start = max(segment['start'], last_end)
            end = max(segment['end'], start + min_duration)  # Ensure minimum duration
            
            # Skip segments that are too short
            if end - start < min_duration:
                continue
                
            corrected_segments.append({
                'start': start,
                'end': end,
                'text': segment['text'].strip(),
            })
            
            last_end = end
            last_text = segment['text'].strip()
            
        return corrected_segments

    # 调整时间戳以匹配实际语音
    def adjust_timestamps(
        self, 
        segments: List[Dict], 
        first_start: float, 
        first_end: float
    ) -> List[Dict]:
        if not segments:
            return []
            
        # 调整第一个片段
        segments[0]['start'] = first_start
        segments[0]['end'] = first_end
        
        # 计算时间偏移
        time_offset = first_end - segments[0]['end']
        
        # 调整后续片段
        adjusted_segments = [segments[0]]
        for segment in segments[1:]:
            adjusted_segments.append({
                'start': segment['start'] + time_offset,
                'end': segment['end'] + time_offset,
                'text': segment['text']
            })
            
        return adjusted_segments

    # 清理文本内容
    def cleanup_text(self, text: str, to_simplified: bool = True) -> str:
        if to_simplified:
            text = self.cc.convert(text)
        
        # 移除多余的空白字符
        text = ' '.join(text.split())
        
        # 移除可能的特殊字符
        text = text.replace('\u200b', '')  # 移除零宽空格
        
        return text.strip()

    # 转录视频
    def transcribe_video(self, video_path: str) -> Optional[Dict]:
        """转录视频的音频内容"""
        try:
            print(f"Starting transcription with Whisper model on {self.device}")
            
            # 使用Whisper模型进行转录
            result = self.whisper_model.transcribe(
                video_path,
                **self.transcribe_options
            )
            
            if not result or not isinstance(result, dict):
                print("Transcription failed: Invalid result format")
                return None
            
            # 验证结果格式
            if 'text' not in result or 'segments' not in result:
                print("Transcription failed: Missing required fields")
                return None
            
            # 处理每个片段的文本
            for segment in result['segments']:
                if 'text' in segment:
                    # 如果需要，转换为简体中文
                    try:
                        segment['text'] = self.cc.convert(segment['text'].strip())
                    except Exception as e:
                        print(f"Error converting text: {e}")
                        segment['text'] = segment['text'].strip()
            
            return result
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return None