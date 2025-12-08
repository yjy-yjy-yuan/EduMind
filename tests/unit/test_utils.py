"""
单元测试 - 工具类函数
测试 utils 目录下的工具函数
"""

import pytest


class TestSubtitleUtils:
    """字幕工具函数测试"""

    def test_format_timestamp_srt(self, app):
        """测试 SRT 格式时间戳"""
        from app.utils.subtitle_utils import format_timestamp

        assert format_timestamp(0, 'srt') == "00:00"
        assert format_timestamp(65, 'srt') == "01:05"
        assert format_timestamp(3661, 'srt') == "61:01"  # 超过1小时

    def test_format_timestamp_vtt(self, app):
        """测试 VTT 格式时间戳"""
        from app.utils.subtitle_utils import format_timestamp

        assert format_timestamp(0, 'vtt') == "00:00"
        assert format_timestamp(90, 'vtt') == "01:30"

    def test_format_timestamp_default(self, app):
        """测试默认格式时间戳"""
        from app.utils.subtitle_utils import format_timestamp

        result = format_timestamp(125, 'other')
        assert result == "[02:05]"

    def test_validate_subtitle_time_valid(self, app):
        """测试有效的字幕时间"""
        from app.utils.subtitle_utils import validate_subtitle_time

        valid, error = validate_subtitle_time(0, 10)
        assert valid is True
        assert error is None

    def test_validate_subtitle_time_negative_start(self, app):
        """测试负数开始时间"""
        from app.utils.subtitle_utils import validate_subtitle_time

        valid, error = validate_subtitle_time(-1, 10)
        assert valid is False
        assert "不能小于0" in error

    def test_validate_subtitle_time_end_before_start(self, app):
        """测试结束时间小于开始时间"""
        from app.utils.subtitle_utils import validate_subtitle_time

        valid, error = validate_subtitle_time(10, 5)
        assert valid is False
        assert "必须大于" in error

    def test_validate_subtitle_time_exceeds_duration(self, app):
        """测试结束时间超过视频时长"""
        from app.utils.subtitle_utils import validate_subtitle_time

        valid, error = validate_subtitle_time(0, 100, video_duration=60)
        assert valid is False
        assert "不能超过" in error

    def test_merge_subtitles_empty(self, app):
        """测试空字幕合并"""
        from app.utils.subtitle_utils import merge_subtitles

        result = merge_subtitles([])
        assert result == []

    def test_merge_subtitles_adjacent_same_text(self, app):
        """测试相邻相同文本字幕合并"""
        from app.utils.subtitle_utils import merge_subtitles

        subtitles = [
            {'text': 'Hello', 'start_time': 0, 'end_time': 5},
            {'text': 'Hello', 'start_time': 5, 'end_time': 10},
        ]
        result = merge_subtitles(subtitles)
        assert len(result) == 1
        assert result[0]['start_time'] == 0
        assert result[0]['end_time'] == 10

    def test_merge_subtitles_different_text(self, app):
        """测试不同文本字幕不合并"""
        from app.utils.subtitle_utils import merge_subtitles

        subtitles = [
            {'text': 'Hello', 'start_time': 0, 'end_time': 5},
            {'text': 'World', 'start_time': 5, 'end_time': 10},
        ]
        result = merge_subtitles(subtitles)
        assert len(result) == 2


class TestVideoUtils:
    """视频工具函数测试"""

    def test_is_valid_url_valid(self, app):
        """测试有效 URL"""
        from app.utils.video_utils import is_valid_url

        assert is_valid_url("https://www.bilibili.com/video/BV123") is True
        assert is_valid_url("http://example.com") is True

    def test_is_valid_url_invalid(self, app):
        """测试无效 URL"""
        from app.utils.video_utils import is_valid_url

        assert is_valid_url("not-a-url") is False
        assert is_valid_url("") is False

    def test_is_bilibili_url(self, app):
        """测试 B 站 URL 识别"""
        from app.utils.video_utils import is_bilibili_url

        assert is_bilibili_url("https://www.bilibili.com/video/BV123") is True
        assert is_bilibili_url("https://b23.tv/abc") is False  # 短链接不包含 bilibili.com
        assert is_bilibili_url("https://youtube.com/watch?v=123") is False

    def test_is_youtube_url(self, app):
        """测试 YouTube URL 识别"""
        from app.utils.video_utils import is_youtube_url

        assert is_youtube_url("https://www.youtube.com/watch?v=123") is True
        assert is_youtube_url("https://youtu.be/123") is True
        assert is_youtube_url("https://bilibili.com") is False

    def test_extract_bv_from_url(self, app):
        """测试从 URL 提取 BV 号"""
        from app.utils.video_utils import extract_bv_from_url

        bv = extract_bv_from_url("https://www.bilibili.com/video/BV1xx411c7XW")
        assert bv == "BV1xx411c7XW"

    def test_extract_bv_from_url_not_found(self, app):
        """测试 URL 中无 BV 号"""
        from app.utils.video_utils import extract_bv_from_url

        with pytest.raises(Exception) as exc_info:
            extract_bv_from_url("https://www.bilibili.com/video/av123")
        assert "未找到BV号" in str(exc_info.value)


class TestSubtitleConversion:
    """字幕格式转换测试"""

    @pytest.fixture
    def mock_subtitles(self):
        """模拟字幕数据"""

        class MockSubtitle:
            def __init__(self, start, end, text):
                self.start_time = start
                self.end_time = end
                self.text = text

        return [
            MockSubtitle(0, 5, "第一条字幕"),
            MockSubtitle(5, 10, "第二条字幕"),
            MockSubtitle(10, 15, "第三条字幕"),
        ]

    def test_convert_to_srt(self, app, mock_subtitles):
        """测试转换为 SRT 格式"""
        from app.utils.subtitle_utils import convert_to_srt

        result = convert_to_srt(mock_subtitles)
        assert "1\n" in result
        assert "第一条字幕" in result
        assert "00:00" in result

    def test_convert_to_vtt(self, app, mock_subtitles):
        """测试转换为 VTT 格式"""
        from app.utils.subtitle_utils import convert_to_vtt

        result = convert_to_vtt(mock_subtitles)
        assert "WEBVTT" in result
        assert "第一条字幕" in result

    def test_convert_to_txt(self, app, mock_subtitles):
        """测试转换为纯文本"""
        from app.utils.subtitle_utils import convert_to_txt

        result = convert_to_txt(mock_subtitles)
        assert "第一条字幕" in result
        assert "第二条字幕" in result
        # 纯文本不包含时间戳
        assert "00:00" not in result

    def test_convert_to_tsv(self, app, mock_subtitles):
        """测试转换为 TSV 格式"""
        from app.utils.subtitle_utils import convert_to_tsv

        result = convert_to_tsv(mock_subtitles)
        assert "start\tend\ttext" in result
        assert "0\t5\t第一条字幕" in result
