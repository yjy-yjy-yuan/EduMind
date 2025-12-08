def format_timestamp(seconds, format='srt'):
    """将秒数转换为不同格式的时间戳"""
    # 四舍五入到整数秒
    seconds = round(seconds)
    minutes = seconds // 60
    seconds = seconds % 60

    if format == 'srt':
        return f"{minutes:02d}:{seconds:02d}"
    elif format == 'vtt':
        return f"{minutes:02d}:{seconds:02d}"
    else:  # 普通时间戳格式 [MM:SS]
        return f"[{minutes:02d}:{seconds:02d}]"


def convert_to_srt(subtitles):
    """将字幕转换为SRT格式"""
    srt_content = []
    for i, subtitle in enumerate(subtitles, 1):
        start_mm = int(float(subtitle.start_time) // 60)
        start_ss = int(float(subtitle.start_time) % 60)
        end_mm = int(float(subtitle.end_time) // 60)
        end_ss = int(float(subtitle.end_time) % 60)

        srt_content.append(f"{i}\n{start_mm:02d}:{start_ss:02d} - {end_mm:02d}:{end_ss:02d}\n{subtitle.text}\n")

    return "\n".join(srt_content)


def convert_to_vtt(subtitles):
    """将字幕转换为VTT格式"""
    vtt_content = ["WEBVTT\n"]
    for subtitle in subtitles:
        start_mm = int(float(subtitle.start_time) // 60)
        start_ss = int(float(subtitle.start_time) % 60)
        end_mm = int(float(subtitle.end_time) // 60)
        end_ss = int(float(subtitle.end_time) % 60)

        vtt_content.append(f"{start_mm:02d}:{start_ss:02d} - {end_mm:02d}:{end_ss:02d}\n{subtitle.text}\n")

    return "\n".join(vtt_content)


def convert_to_txt(subtitles):
    """将字幕转换为纯文本格式"""
    return "\n".join(s.text for s in subtitles)


def convert_to_tsv(subtitles):
    """将字幕转换为TSV格式"""
    tsv_content = ["start\tend\ttext"]
    for subtitle in subtitles:
        # 将时间从毫秒转换为秒
        start_time = int(float(subtitle.start_time))
        end_time = int(float(subtitle.end_time))
        tsv_content.append(f"{start_time}\t{end_time}\t{subtitle.text}")

    return "\n".join(tsv_content)


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
        if current['text'] == next_sub['text'] and current['end_time'] == next_sub['start_time']:
            current['end_time'] = next_sub['end_time']
        else:
            merged.append(current)
            current = next_sub.copy()

    merged.append(current)
    return merged
