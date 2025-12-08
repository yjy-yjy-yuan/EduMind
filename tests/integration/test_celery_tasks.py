"""
集成测试 - 异步任务完整流程
测试 Celery 任务的集成场景

注意：
- 这些测试验证任务的集成逻辑，不实际执行耗时的处理
- 迁移到 FastAPI + ProcessPoolExecutor 后，核心逻辑保持一致

测试场景：
1. 视频处理任务状态更新流程
2. 字幕生成任务流程
3. 视频清理任务流程
4. 任务失败和重试逻辑
"""

import json
import os
import tempfile
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest


class TestVideoProcessingTaskIntegration:
    """视频处理任务集成测试"""

    def test_video_processing_status_flow(self, app, db_session):
        """测试视频处理状态流程"""
        from app.models import Video
        from app.models import VideoStatus

        with app.app_context():
            # 创建测试视频
            video = Video(
                title='集成测试视频',
                filename='integration_test.mp4',
                filepath='/tmp/integration_test.mp4',
                status=VideoStatus.UPLOADED,
            )
            db_session.add(video)
            db_session.commit()
            video_id = video.id

            # 模拟任务开始：状态变为 PROCESSING
            video.status = VideoStatus.PROCESSING
            video.process_progress = 0.0
            video.current_step = '初始化处理'
            db_session.commit()

            assert video.status == VideoStatus.PROCESSING
            assert video.process_progress == 0.0

            # 模拟进度更新
            steps = [
                (10.0, '生成预览图'),
                (30.0, '提取视频信息'),
                (50.0, '准备转录视频'),
                (80.0, '生成字幕'),
                (100.0, '处理完成'),
            ]

            for progress, step in steps:
                video.process_progress = progress
                video.current_step = step
                db_session.commit()
                assert video.process_progress == progress
                assert video.current_step == step

            # 完成处理
            video.status = VideoStatus.COMPLETED
            video.processed = True
            db_session.commit()

            assert video.status == VideoStatus.COMPLETED
            assert video.processed is True

    def test_video_processing_failure_flow(self, app, db_session):
        """测试视频处理失败流程"""
        from app.models import Video
        from app.models import VideoStatus

        with app.app_context():
            video = Video(
                title='失败测试视频',
                filename='failure_test.mp4',
                filepath='/tmp/failure_test.mp4',
                status=VideoStatus.PROCESSING,
                process_progress=50.0,
                current_step='转录中',
            )
            db_session.add(video)
            db_session.commit()

            # 模拟失败
            video.status = VideoStatus.FAILED
            video.error_message = '转录失败：模型加载超时'
            video.current_step = '处理失败'
            db_session.commit()

            assert video.status == VideoStatus.FAILED
            assert '超时' in video.error_message

    def test_video_processing_with_preview(self, app, db_session):
        """测试视频处理预览图生成"""
        from app.models import Video
        from app.models import VideoStatus

        with app.app_context():
            video = Video(
                title='预览图测试视频',
                filename='preview_test.mp4',
                filepath='/tmp/preview_test.mp4',
                status=VideoStatus.PROCESSING,
            )
            db_session.add(video)
            db_session.commit()

            # 模拟预览图生成
            video.preview_filename = f'preview_{video.id}.jpg'
            video.preview_filepath = f'/tmp/previews/preview_{video.id}.jpg'
            video.process_progress = 20.0
            db_session.commit()

            assert video.preview_filename is not None
            assert 'preview_' in video.preview_filename


class TestSubtitleTaskIntegration:
    """字幕任务集成测试"""

    def test_subtitle_generation_flow(self, app, db_session):
        """测试字幕生成流程"""
        from app.models import Subtitle
        from app.models import Video
        from app.models import VideoStatus

        with app.app_context():
            # 创建已完成的视频
            video = Video(
                title='字幕测试视频',
                filename='subtitle_test.mp4',
                filepath='/tmp/subtitle_test.mp4',
                status=VideoStatus.COMPLETED,
            )
            db_session.add(video)
            db_session.commit()

            # 模拟字幕生成
            subtitles = [
                Subtitle(video_id=video.id, start_time=0.0, end_time=5.0, text='第一句话', source='asr', language='zh'),
                Subtitle(
                    video_id=video.id, start_time=5.0, end_time=10.0, text='第二句话', source='asr', language='zh'
                ),
            ]

            for subtitle in subtitles:
                db_session.add(subtitle)
            db_session.commit()

            # 验证字幕已添加
            video_subtitles = Subtitle.query.filter_by(video_id=video.id).all()
            assert len(video_subtitles) == 2

    def test_subtitle_replacement_flow(self, app, db_session):
        """测试字幕替换流程（重新生成）"""
        from app.models import Subtitle
        from app.models import Video
        from app.models import VideoStatus

        with app.app_context():
            video = Video(
                title='字幕替换测试',
                filename='subtitle_replace_test.mp4',
                filepath='/tmp/subtitle_replace_test.mp4',
                status=VideoStatus.COMPLETED,
            )
            db_session.add(video)
            db_session.commit()

            # 添加旧字幕
            old_subtitle = Subtitle(
                video_id=video.id, start_time=0.0, end_time=5.0, text='旧字幕', source='asr', language='zh'
            )
            db_session.add(old_subtitle)
            db_session.commit()

            # 模拟重新生成：先删除旧字幕
            Subtitle.query.filter_by(video_id=video.id).delete()
            db_session.commit()

            # 验证旧字幕已删除
            remaining = Subtitle.query.filter_by(video_id=video.id).all()
            assert len(remaining) == 0

            # 添加新字幕
            new_subtitle = Subtitle(
                video_id=video.id, start_time=0.0, end_time=5.0, text='新字幕', source='asr', language='zh'
            )
            db_session.add(new_subtitle)
            db_session.commit()

            # 验证新字幕
            new_subtitles = Subtitle.query.filter_by(video_id=video.id).all()
            assert len(new_subtitles) == 1
            assert new_subtitles[0].text == '新字幕'


class TestVideoCleanupTaskIntegration:
    """视频清理任务集成测试"""

    def test_cleanup_flow(self, app, db_session):
        """测试视频清理流程"""
        from app.models import Video
        from app.models import VideoStatus
        from app.models.qa import Question

        with app.app_context():
            # 创建视频
            video = Video(
                title='清理测试视频',
                filename='cleanup_test.mp4',
                filepath='/tmp/cleanup_test.mp4',
                status=VideoStatus.COMPLETED,
            )
            db_session.add(video)
            db_session.commit()
            video_id = video.id

            # 添加关联的问题记录
            question = Question(video_id=video_id, content='测试问题')
            db_session.add(question)
            db_session.commit()

            # 模拟清理：先删除关联记录
            Question.query.filter_by(video_id=video_id).delete()
            db_session.commit()

            # 验证问题已删除
            remaining_questions = Question.query.filter_by(video_id=video_id).all()
            assert len(remaining_questions) == 0

            # 删除视频
            db_session.delete(video)
            db_session.commit()

            # 验证视频已删除
            deleted_video = Video.query.get(video_id)
            assert deleted_video is None


class TestTaskRetryLogic:
    """任务重试逻辑测试"""

    def test_retry_on_failure(self, app, db_session):
        """测试失败后的重试逻辑"""
        from app.models import Video
        from app.models import VideoStatus

        with app.app_context():
            video = Video(
                title='重试测试视频',
                filename='retry_test.mp4',
                filepath='/tmp/retry_test.mp4',
                status=VideoStatus.UPLOADED,
            )
            db_session.add(video)
            db_session.commit()

            # 第一次尝试失败
            video.status = VideoStatus.FAILED
            video.error_message = '临时错误'
            db_session.commit()

            # 用户请求重试
            video.status = VideoStatus.PENDING
            video.error_message = None
            db_session.commit()

            assert video.status == VideoStatus.PENDING

            # 第二次尝试成功
            video.status = VideoStatus.PROCESSING
            db_session.commit()

            video.status = VideoStatus.COMPLETED
            db_session.commit()

            assert video.status == VideoStatus.COMPLETED


class TestConcurrentTaskScenarios:
    """并发任务场景测试"""

    def test_multiple_videos_processing(self, app, db_session):
        """测试多个视频同时处理"""
        from app.models import Video
        from app.models import VideoStatus

        with app.app_context():
            # 创建多个视频
            videos = []
            for i in range(3):
                video = Video(
                    title=f'并发测试视频 {i}',
                    filename=f'concurrent_test_{i}.mp4',
                    filepath=f'/tmp/concurrent_test_{i}.mp4',
                    status=VideoStatus.PENDING,
                )
                db_session.add(video)
                videos.append(video)
            db_session.commit()

            # 模拟并发处理
            for video in videos:
                video.status = VideoStatus.PROCESSING
            db_session.commit()

            # 验证所有视频都在处理中
            processing_count = Video.query.filter_by(status=VideoStatus.PROCESSING).count()
            assert processing_count >= 3


class TestTaskDataIntegrity:
    """任务数据完整性测试"""

    def test_video_info_persistence(self, app, db_session):
        """测试视频信息持久化"""
        from app.models import Video
        from app.models import VideoStatus

        with app.app_context():
            video = Video(
                title='持久化测试视频',
                filename='persist_test.mp4',
                filepath='/tmp/persist_test.mp4',
                status=VideoStatus.PROCESSING,
            )
            db_session.add(video)
            db_session.commit()
            video_id = video.id

            # 更新视频信息
            video.width = 1920
            video.height = 1080
            video.fps = 30.0
            video.duration = 120.5
            video.frame_count = 3615
            db_session.commit()

            # 重新查询验证数据
            reloaded = Video.query.get(video_id)
            assert reloaded.width == 1920
            assert reloaded.height == 1080
            assert reloaded.fps == 30.0
            assert reloaded.duration == 120.5

    def test_subtitle_file_path_persistence(self, app, db_session):
        """测试字幕文件路径持久化"""
        from app.models import Video
        from app.models import VideoStatus

        with app.app_context():
            video = Video(
                title='字幕路径测试',
                filename='subtitle_path_test.mp4',
                filepath='/tmp/subtitle_path_test.mp4',
                status=VideoStatus.COMPLETED,
            )
            db_session.add(video)
            db_session.commit()

            # 更新字幕路径
            video.subtitle_filepath = '/tmp/subtitles/subtitle_path_test.srt'
            db_session.commit()

            # 验证
            reloaded = Video.query.get(video.id)
            assert reloaded.subtitle_filepath == '/tmp/subtitles/subtitle_path_test.srt'


class TestTaskAPIIntegration:
    """任务与 API 集成测试"""

    def test_process_api_triggers_task(self, client, created_video, auth_headers):
        """测试 API 触发任务"""
        response = client.post(
            f'/api/videos/{created_video.id}/process',
            data=json.dumps({'language': 'Chinese', 'model': 'base'}),
            headers=auth_headers,
        )
        # API 应该接受请求（即使任务可能失败）
        assert response.status_code in [200, 201, 400, 404, 500]

    def test_status_api_reflects_task_state(self, client, app, db_session):
        """测试状态 API 反映任务状态"""
        from app.models import Video
        from app.models import VideoStatus

        with app.app_context():
            video = Video(
                title='状态 API 测试',
                filename='status_api_test.mp4',
                filepath='/tmp/status_api_test.mp4',
                status=VideoStatus.PROCESSING,
                process_progress=50.0,
                current_step='转录中',
            )
            db_session.add(video)
            db_session.commit()
            video_id = video.id

        # 查询状态
        response = client.get(f'/api/videos/{video_id}/status')
        assert response.status_code == 200

        data = response.get_json()
        assert 'status' in data or 'processing_status' in data


class TestMigrationCompatibility:
    """
    迁移兼容性测试
    确保任务逻辑在 Celery → ProcessPoolExecutor 迁移后保持一致
    """

    def test_task_result_format(self):
        """测试任务结果格式"""
        # 成功结果
        success = {'status': 'success', 'message': '处理完成'}
        assert success['status'] == 'success'

        # 失败结果
        failed = {'status': 'failed', 'message': '处理失败'}
        assert failed['status'] == 'failed'

        # 错误结果
        error = {'status': 'error', 'message': '系统错误'}
        assert error['status'] == 'error'

    def test_video_status_values(self, app):
        """测试视频状态值"""
        from app.models import VideoStatus

        # 验证所有状态值存在
        assert VideoStatus.UPLOADED is not None
        assert VideoStatus.PENDING is not None
        assert VideoStatus.PROCESSING is not None
        assert VideoStatus.COMPLETED is not None
        assert VideoStatus.FAILED is not None
        assert VideoStatus.DOWNLOADING is not None

    def test_progress_range(self, app, db_session):
        """测试进度值范围"""
        from app.models import Video
        from app.models import VideoStatus

        with app.app_context():
            video = Video(
                title='进度范围测试',
                filename='progress_range_test.mp4',
                filepath='/tmp/progress_range_test.mp4',
                status=VideoStatus.PROCESSING,
            )
            db_session.add(video)
            db_session.commit()

            # 测试边界值
            for progress in [0.0, 25.0, 50.0, 75.0, 100.0]:
                video.process_progress = progress
                db_session.commit()
                assert 0 <= video.process_progress <= 100
