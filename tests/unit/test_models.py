"""
单元测试 - 数据模型测试
测试 Video, Note, Subtitle 等模型的基本功能
"""
import pytest
from datetime import datetime


class TestVideoModel:
    """Video 模型测试"""

    def test_create_video(self, app, db_session):
        """测试创建视频记录"""
        from app.models import Video

        video = Video(
            title='测试视频',
            filepath='/uploads/test.mp4',
            duration=120
        )
        db_session.add(video)
        db_session.commit()

        assert video.id is not None
        assert video.title == '测试视频'
        assert video.duration == 120

    def test_video_default_status(self, app, db_session):
        """测试视频默认状态"""
        from app.models import Video, VideoStatus

        video = Video(
            title='测试视频',
            filepath='/uploads/test.mp4'
        )
        db_session.add(video)
        db_session.commit()

        # 默认状态应为 UPLOADED
        assert video.status == VideoStatus.UPLOADED

    def test_video_to_dict(self, app, db_session):
        """测试视频转字典"""
        from app.models import Video

        video = Video(
            title='测试视频',
            filepath='/uploads/test.mp4',
            duration=120
        )
        db_session.add(video)
        db_session.commit()

        video_dict = video.to_dict()
        assert 'id' in video_dict
        assert 'title' in video_dict
        assert video_dict['title'] == '测试视频'

    def test_video_status_change(self, app, db_session):
        """测试视频状态变更"""
        from app.models import Video, VideoStatus

        video = Video(title='测试视频', filepath='/test.mp4')
        db_session.add(video)
        db_session.commit()

        # 更改状态为处理中
        video.status = VideoStatus.PROCESSING
        db_session.commit()

        assert video.status == VideoStatus.PROCESSING


class TestNoteModel:
    """Note 模型测试"""

    def test_create_note(self, app, db_session):
        """测试创建笔记"""
        from app.models import Note

        note = Note(
            title='测试笔记',
            content='这是笔记内容'
        )
        db_session.add(note)
        db_session.commit()

        assert note.id is not None
        assert note.title == '测试笔记'

    def test_note_created_at(self, app, db_session):
        """测试笔记创建时间"""
        from app.models import Note

        note = Note(
            title='测试笔记',
            content='内容'
        )
        db_session.add(note)
        db_session.commit()

        assert note.created_at is not None
        assert isinstance(note.created_at, datetime)

    def test_note_to_dict(self, app, db_session):
        """测试笔记转字典"""
        from app.models import Note

        note = Note(
            title='测试笔记',
            content='内容',
            tags='标签1,标签2'
        )
        db_session.add(note)
        db_session.commit()

        note_dict = note.to_dict()
        assert note_dict['title'] == '测试笔记'
        assert note_dict['tags'] == ['标签1', '标签2']


class TestSubtitleModel:
    """Subtitle 模型测试"""

    def test_create_subtitle(self, app, db_session):
        """测试创建字幕"""
        from app.models import Video, Subtitle

        # 先创建视频
        video = Video(title='测试视频', filepath='/test.mp4')
        db_session.add(video)
        db_session.commit()

        # 创建字幕（使用正确的字段名）
        subtitle = Subtitle(
            video_id=video.id,
            start_time=0.0,
            end_time=5.0,
            text='这是字幕内容',
            source='asr',
            language='zh'
        )
        db_session.add(subtitle)
        db_session.commit()

        assert subtitle.id is not None
        assert subtitle.video_id == video.id

    def test_subtitle_time_range(self, app, db_session):
        """测试字幕时间范围"""
        from app.models import Video, Subtitle

        video = Video(title='测试视频', filepath='/test.mp4')
        db_session.add(video)
        db_session.commit()

        subtitle = Subtitle(
            video_id=video.id,
            start_time=10.5,
            end_time=15.5,
            text='字幕',
            source='asr',
            language='zh'
        )
        db_session.add(subtitle)
        db_session.commit()

        assert subtitle.start_time == 10.5
        assert subtitle.end_time == 15.5
        assert subtitle.end_time > subtitle.start_time

    def test_subtitle_to_dict(self, app, db_session):
        """测试字幕转字典"""
        from app.models import Video, Subtitle

        video = Video(title='测试视频', filepath='/test.mp4')
        db_session.add(video)
        db_session.commit()

        subtitle = Subtitle(
            video_id=video.id,
            start_time=0.0,
            end_time=5.0,
            text='字幕内容',
            source='manual',
            language='zh'
        )
        db_session.add(subtitle)
        db_session.commit()

        sub_dict = subtitle.to_dict()
        assert sub_dict['text'] == '字幕内容'
        assert sub_dict['source'] == 'manual'
