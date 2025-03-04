from datetime import timedelta
import re

def parse_srt_file(filepath):
    """解析SRT格式的字幕文件
    
    Args:
        filepath (str): SRT文件路径
        
    Returns:
        list: 包含字幕信息的字典列表，每个字典包含：
            - start_time: 开始时间（秒）
            - end_time: 结束时间（秒）
            - text: 字幕文本
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 分割字幕块
        subtitle_blocks = re.split(r'\n\n+', content.strip())
        subtitles = []
        
        for block in subtitle_blocks:
            lines = block.split('\n')
            if len(lines) < 3:  # 跳过无效块
                continue
                
            # 解析时间戳
            times = lines[1].split(' --> ')
            if len(times) != 2:
                continue
                
            # 将时间戳转换为秒
            start_time = _timestamp_to_seconds(times[0].strip())
            end_time = _timestamp_to_seconds(times[1].strip())
            
            # 获取文本（可能跨多行）
            text = ' '.join(lines[2:]).strip()
            
            subtitles.append({
                'start_time': start_time,
                'end_time': end_time,
                'text': text
            })
            
        return subtitles
        
    except Exception as e:
        print(f"解析SRT文件失败: {str(e)}")
        return None

def _timestamp_to_seconds(timestamp):
    """将SRT时间戳转换为秒数
    
    Args:
        timestamp (str): 格式为 "HH:MM:SS,mmm"
        
    Returns:
        float: 秒数
    """
    # 移除毫秒
    parts = timestamp.replace(',', '.').split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds

def format_timestamp(seconds, format='srt'):
    """将秒数转换为不同格式的时间戳"""
    # 四舍五入到整数秒
    seconds = round(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if format == 'srt':
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    elif format == 'vtt':
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:  # 普通时间戳格式 [HH:MM:SS]
        return f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"

def convert_to_srt(subtitles):
    """将字幕转换为SRT格式"""
    srt_content = ""
    for i, subtitle in enumerate(subtitles, 1):
        start_time = format_timestamp(subtitle['start_time'], 'srt')
        end_time = format_timestamp(subtitle['end_time'], 'srt')
        srt_content += f"{i}\n{start_time} --> {end_time}\n{subtitle['text']}\n\n"
    return srt_content

def convert_to_vtt(subtitles):
    """将字幕转换为VTT格式"""
    vtt_content = "WEBVTT\n\n"
    for i, subtitle in enumerate(subtitles, 1):
        start_time = format_timestamp(subtitle['start_time'], 'vtt')
        end_time = format_timestamp(subtitle['end_time'], 'vtt')
        vtt_content += f"{start_time} --> {end_time}\n{subtitle['text']}\n\n"
    return vtt_content

def convert_to_txt(subtitles):
    """将字幕转换为纯文本格式"""
    txt_content = ""
    for subtitle in subtitles:
        timestamp = format_timestamp(subtitle['start_time'], 'txt')
        txt_content += f"{timestamp} {subtitle['text']}\n"
    return txt_content

def validate_subtitle_time(start_time, end_time, video_duration=None):
    """验证字幕时间是否有效"""
    # 四舍五入到整数秒
    start_time = round(start_time)
    end_time = round(end_time)
    if video_duration:
        video_duration = round(video_duration)
        
    if start_time < 0:
        return False, "开始时间不能小于0"
    if end_time <= start_time:
        return False, "结束时间必须大于开始时间"
    if video_duration and end_time > video_duration:
        return False, f"结束时间不能超过视频时长 ({video_duration}秒)"
    return True, None

def merge_subtitles(subtitles):
    """合并相邻的重复字幕"""
    if not subtitles:
        return []
    
    # 四舍五入所有时间戳到整数秒
    for sub in subtitles:
        sub['start_time'] = round(sub['start_time'])
        sub['end_time'] = round(sub['end_time'])
    
    merged = []
    current = subtitles[0].copy()
    
    for next_sub in subtitles[1:]:
        # 如果当前字幕和下一个字幕的文本相同且时间相连
        if (current['text'] == next_sub['text'] and 
            current['end_time'] == next_sub['start_time']):
            current['end_time'] = next_sub['end_time']
        else:
            merged.append(current)
            current = next_sub.copy()
    
    merged.append(current)
    return merged
