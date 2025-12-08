"""
视频处理工具类
主要功能：
1. 视频转录（使用whisper）
2. 字幕生成和格式化
3. 简繁体转换
"""

import json
import logging
import subprocess

import cv2
import whisper
from opencc import OpenCC

logger = logging.getLogger(__name__)


class VideoTools:
    """视频处理工具类"""

    def __init__(self, whisper_model="base"):
        """初始化视频工具类"""
        self.model = whisper.load_model(whisper_model)
        self.whisper_model = None
        self.opencc = OpenCC('t2s')  # 繁体转简体

    def transcribe_video(self, video_path):
        """转录视频"""
        try:
            # 使用whisper转录
            result = self.model.transcribe(video_path)
            return result
        except Exception as e:
            print(f"转录视频失败: {str(e)}")
            return None

    def _format_timestamp(self, seconds):
        """格式化时间戳为SRT格式
        Args:
            seconds: 秒数
        Returns:
            str: SRT格式时间戳，例如: 01:30
        """
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def format_timestamp(self, seconds):
        """格式化时间戳"""
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def create_paragraphs(self, transcript, to_simplified=True):
        """创建带时间戳的段落"""
        try:
            segments = []
            for segment in transcript:
                # 将时间从毫秒转换为秒
                start_time = float(segment.get('start', 0)) / 1000
                end_time = float(segment.get('end', 0)) / 1000

                text = segment.get('text', '').strip()
                if to_simplified:
                    text = self.opencc.convert(text)

                segments.append({'start': start_time, 'end': end_time, 'text': text})
            return segments
        except Exception as e:
            logger.error(f"创建段落失败: {str(e)}")
            return []

    def save_as_srt(self, segments, output_path, to_simplified=True):
        """保存为SRT格式字幕文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments, 1):
                    start_mm = int(float(segment['start']) // 60)
                    start_ss = int(float(segment['start']) % 60)
                    end_mm = int(float(segment['end']) // 60)
                    end_ss = int(float(segment['end']) % 60)

                    text = segment['text']
                    if to_simplified:
                        text = self.opencc.convert(text)

                    f.write(f"{i}\n")
                    f.write(f"{start_mm:02d}:{start_ss:02d} - {end_mm:02d}:{end_ss:02d}\n")
                    f.write(f"{text}\n\n")
            return True
        except Exception as e:
            logger.error(f"保存SRT字幕文件失败: {str(e)}")
            return False

    def save_as_vtt(self, segments, output_path, to_simplified=True):
        """保存为VTT格式字幕文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                for segment in segments:
                    start_mm = int(float(segment['start']) // 60)
                    start_ss = int(float(segment['start']) % 60)
                    end_mm = int(float(segment['end']) // 60)
                    end_ss = int(float(segment['end']) % 60)

                    text = segment['text']
                    if to_simplified:
                        text = self.opencc.convert(text)

                    f.write(f"{start_mm:02d}:{start_ss:02d} - {end_mm:02d}:{end_ss:02d}\n")
                    f.write(f"{text}\n\n")
            return True
        except Exception as e:
            logger.error(f"保存VTT字幕文件失败: {str(e)}")
            return False

    def save_as_tsv(self, segments, output_path, to_simplified=True):
        """保存为TSV格式字幕文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("start\tend\ttext\n")
                for segment in segments:
                    # 将时间从毫秒转换为秒
                    start_time = int(float(segment['start']))
                    end_time = int(float(segment['end']))

                    text = segment['text']
                    if to_simplified:
                        text = self.opencc.convert(text)

                    f.write(f"{start_time}\t{end_time}\t{text}\n")
            return True
        except Exception as e:
            logger.error(f"保存TSV字幕文件失败: {str(e)}")
            return False

    def save_subtitles(self, result, txt_path, srt_path, to_simplified=True):
        """保存字幕文件（TXT和SRT格式）"""
        try:
            # 保存TXT格式（带时间戳的段落）
            paragraphs = self.create_paragraphs(result, to_simplified)
            with open(txt_path, 'w', encoding='utf-8') as f:
                for segment in paragraphs:
                    start_time = segment['start']
                    end_time = segment['end']

                    # 格式化时间戳
                    start_formatted = self.format_timestamp(start_time)
                    end_formatted = self.format_timestamp(end_time)

                    # 处理文本
                    text = segment['text'].strip()

                    # 使用方括号包裹时间戳
                    formatted_line = f"[{start_formatted} --> {end_formatted}] {text}\n\n"
                    f.write(formatted_line)

            # 保存SRT格式
            self.save_as_srt(paragraphs, srt_path, to_simplified)

            return True

        except Exception as e:
            print(f"保存字幕文件失败: {str(e)}")
            return False

    def generate_preview(self, video_path, output_path):
        """生成视频预览图
        Args:
            video_path: 视频文件路径
            output_path: 输出图片路径
        Returns:
            bool: 是否成功
        """
        try:
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("无法打开视频文件")

            # 获取视频总帧数
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames == 0:
                raise Exception("视频帧数为0")

            # 跳转到视频中间位置
            middle_frame = total_frames // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)

            # 读取帧
            ret, frame = cap.read()
            if not ret:
                raise Exception("无法读取视频帧")

            # 保存图片
            cv2.imwrite(output_path, frame)

            # 释放资源
            cap.release()

            logger.info(f"生成预览图成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"生成预览图失败: {str(e)}")
            return False

    def get_video_info(self, video_path):
        """获取视频信息
        Args:
            video_path: 视频文件路径
        Returns:
            dict: 视频信息，包含duration, fps, width, height, frame_count
        """
        try:
            # 使用ffprobe获取视频信息
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', video_path]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"ffprobe执行失败: {result.stderr}")

            # 解析JSON输出
            info = json.loads(result.stdout)

            # 获取视频流信息
            video_stream = None
            for stream in info['streams']:
                if stream['codec_type'] == 'video':
                    video_stream = stream
                    break

            if not video_stream:
                raise Exception("未找到视频流")

            # 提取信息
            duration = float(info['format']['duration'])
            fps = eval(video_stream['r_frame_rate'])  # 例如: '30000/1001'
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            frame_count = int(video_stream['nb_frames'])

            return {'duration': duration, 'fps': fps, 'width': width, 'height': height, 'frame_count': frame_count}

        except Exception as e:
            logger.error(f"获取视频信息失败: {str(e)}")
            return {}

    def generate_subtitles(self, video_path, output_path, model_name="base"):
        """生成字幕文件
        Args:
            video_path: 视频文件路径
            output_path: 输出字幕文件路径
            model_name: whisper模型名称
        Returns:
            bool: 是否成功
        """
        try:
            # 加载whisper模型
            if self.whisper_model is None:
                self.whisper_model = whisper.load_model(model_name)

            # 转录音频
            result = self.whisper_model.transcribe(video_path)

            # 生成SRT格式字幕
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(result['segments'], 1):
                    # 转换时间戳
                    start = self._format_timestamp(segment['start'])
                    end = self._format_timestamp(segment['end'])

                    # 转换繁体到简体
                    text = self.opencc.convert(segment['text'].strip())

                    # 写入SRT格式
                    f.write(f"{i}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")

            logger.info(f"生成字幕文件成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"生成字幕文件失败: {str(e)}")
            return False
