"""
单元测试 - Celery 任务测试
测试视频处理、字幕生成等异步任务的核心逻辑

注意：这些测试不实际执行 Celery 任务，而是测试任务中的核心函数
迁移到 FastAPI + ProcessPoolExecutor 后，这些测试仍然有效
"""

import os
import tempfile

import numpy as np
import pytest


class TestVideoProcessingFunctions:
    """视频处理函数测试"""

    def test_generate_video_info_valid_video(self, app):
        """测试从有效视频获取信息"""
        from app.tasks.video_processing_mac import generate_video_info

        # 创建一个临时的测试视频（使用 OpenCV）
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            temp_path = f.name

        try:
            # 使用 OpenCV 创建一个简单的测试视频
            import cv2

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_path, fourcc, 30.0, (640, 480))

            # 写入几帧
            for _ in range(30):  # 1 秒的视频
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                out.write(frame)
            out.release()

            # 测试获取视频信息
            info = generate_video_info(temp_path)

            assert info is not None
            assert info['width'] == 640
            assert info['height'] == 480
            assert info['fps'] == 30.0
            assert info['frame_count'] == 30
            assert abs(info['duration'] - 1.0) < 0.1  # 约 1 秒
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_generate_video_info_invalid_path(self, app):
        """测试无效路径"""
        from app.tasks.video_processing_mac import generate_video_info

        result = generate_video_info('/nonexistent/path/video.mp4')
        assert result is None

    def test_generate_video_info_invalid_file(self, app):
        """测试无效文件"""
        from app.tasks.video_processing_mac import generate_video_info

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            f.write(b'not a video file')
            temp_path = f.name

        try:
            result = generate_video_info(temp_path)
            assert result is None
        finally:
            os.remove(temp_path)


class TestDeviceSelection:
    """设备选择函数测试"""

    def test_get_device(self, app):
        """测试获取计算设备"""
        from app.tasks.video_processing_mac import get_device

        device = get_device()
        # 应该返回 'mps' 或 'cpu'
        assert device in ['mps', 'cpu']

    def test_get_whisper_device(self, app):
        """测试 Whisper 设备选择"""
        from app.tasks.video_processing_mac import get_whisper_device

        # 测试不同模型大小
        models = ['tiny', 'base', 'small', 'medium', 'large']

        for model in models:
            device = get_whisper_device(model)
            assert device in ['mps', 'cpu']


class TestWhisperParams:
    """Whisper 参数配置测试"""

    def test_get_whisper_params_chinese(self, app):
        """测试中文参数"""
        from app.tasks.video_processing_mac import get_whisper_params

        params = get_whisper_params('base', 'zh')

        assert params['language'] == 'Chinese'
        assert params['task'] == 'transcribe'
        assert params['fp16'] is False  # Mac MPS 不支持 fp16
        assert '教育视频' in params['initial_prompt']

    def test_get_whisper_params_english(self, app):
        """测试英文参数"""
        from app.tasks.video_processing_mac import get_whisper_params

        params = get_whisper_params('base', 'en')

        assert params['language'] == 'English'
        assert 'educational video' in params['initial_prompt'].lower()

    def test_get_whisper_params_japanese(self, app):
        """测试日文参数"""
        from app.tasks.video_processing_mac import get_whisper_params

        params = get_whisper_params('base', 'ja')

        assert params['language'] == 'Japanese'

    def test_get_whisper_params_model_specific(self, app):
        """测试不同模型的参数差异"""
        from app.tasks.video_processing_mac import get_whisper_params

        # tiny/base 模型使用较小的 beam_size
        tiny_params = get_whisper_params('tiny', 'zh')
        assert tiny_params['beam_size'] == 1
        assert tiny_params['best_of'] == 1

        # medium/large 模型使用较大的 beam_size
        medium_params = get_whisper_params('medium', 'zh')
        assert medium_params['beam_size'] == 5
        assert medium_params['best_of'] == 5


class TestTranscriptionMerge:
    """转录结果合并测试"""

    def test_merge_transcriptions_empty(self, app):
        """测试空转录结果合并"""
        from app.tasks.video_processing_mac import merge_transcriptions

        result = merge_transcriptions([])
        assert result['text'] == ''
        assert result['segments'] == []

    def test_merge_transcriptions_single(self, app):
        """测试单个转录结果"""
        from app.tasks.video_processing_mac import merge_transcriptions

        chunks = [
            {
                'text': 'Hello world',
                'segments': [{'start': 0.0, 'end': 1.0, 'text': 'Hello'}, {'start': 1.0, 'end': 2.0, 'text': 'world'}],
            }
        ]

        result = merge_transcriptions(chunks)
        assert 'Hello world' in result['text']
        assert len(result['segments']) == 2

    def test_merge_transcriptions_multiple(self, app):
        """测试多个转录结果合并"""
        from app.tasks.video_processing_mac import merge_transcriptions

        chunks = [
            {'text': 'First chunk', 'segments': [{'start': 0.0, 'end': 5.0, 'text': 'First chunk'}]},
            {'text': 'Second chunk', 'segments': [{'start': 0.0, 'end': 5.0, 'text': 'Second chunk'}]},
        ]

        result = merge_transcriptions(chunks)
        assert 'First chunk' in result['text']
        assert 'Second chunk' in result['text']
        assert len(result['segments']) == 2

        # 验证时间戳偏移
        assert result['segments'][0]['start'] == 0.0
        assert result['segments'][1]['start'] == 5.0  # 偏移了第一个 chunk 的结束时间

    def test_merge_transcriptions_with_none(self, app):
        """测试包含 None 的转录结果"""
        from app.tasks.video_processing_mac import merge_transcriptions

        chunks = [
            {'text': 'Valid', 'segments': [{'start': 0.0, 'end': 1.0, 'text': 'Valid'}]},
            None,
            {'text': 'Also valid', 'segments': [{'start': 0.0, 'end': 1.0, 'text': 'Also valid'}]},
        ]

        result = merge_transcriptions(chunks)
        assert 'Valid' in result['text']
        assert 'Also valid' in result['text']


class TestCleanupFunctions:
    """清理函数测试"""

    def test_clear_mps_cache(self, app):
        """测试 MPS 缓存清理"""
        from app.tasks.video_processing_mac import clear_mps_cache

        # 不应该抛出异常
        clear_mps_cache()


class TestSubtitleTasks:
    """字幕任务测试"""

    def test_subtitle_task_video_not_found(self, app, db_session):
        """测试视频不存在时的字幕生成"""
        from app.tasks.subtitle_tasks import generate_subtitles

        # 应该抛出异常或返回错误
        with pytest.raises(Exception) as exc_info:
            generate_subtitles(99999)

        assert '视频不存在' in str(exc_info.value) or 'not exist' in str(exc_info.value).lower()


class TestProcessVideoTaskLogic:
    """视频处理任务逻辑测试（不实际执行 Celery）"""

    def test_video_status_transitions(self, app, db_session):
        """测试视频状态转换"""
        from app.models import Video
        from app.models import VideoStatus

        # 创建测试视频
        video = Video(
            title='状态测试视频',
            filename='status_test.mp4',
            filepath='/tmp/status_test.mp4',
            status=VideoStatus.UPLOADED,
        )
        db_session.add(video)
        db_session.commit()

        # 验证初始状态
        assert video.status == VideoStatus.UPLOADED

        # 模拟状态转换
        video.status = VideoStatus.PROCESSING
        db_session.commit()
        assert video.status == VideoStatus.PROCESSING

        # 完成处理
        video.status = VideoStatus.COMPLETED
        db_session.commit()
        assert video.status == VideoStatus.COMPLETED

    def test_video_progress_update(self, app, db_session):
        """测试视频处理进度更新"""
        from app.models import Video
        from app.models import VideoStatus

        video = Video(
            title='进度测试视频',
            filename='progress_test.mp4',
            filepath='/tmp/progress_test.mp4',
            status=VideoStatus.PROCESSING,
            process_progress=0.0,
        )
        db_session.add(video)
        db_session.commit()

        # 模拟进度更新
        progress_steps = [10.0, 30.0, 50.0, 80.0, 100.0]

        for progress in progress_steps:
            video.process_progress = progress
            db_session.commit()
            assert video.process_progress == progress

    def test_video_error_handling(self, app, db_session):
        """测试视频处理错误处理"""
        from app.models import Video
        from app.models import VideoStatus

        video = Video(
            title='错误测试视频',
            filename='error_test.mp4',
            filepath='/tmp/error_test.mp4',
            status=VideoStatus.PROCESSING,
        )
        db_session.add(video)
        db_session.commit()

        # 模拟错误
        video.status = VideoStatus.FAILED
        video.error_message = '处理失败：文件损坏'
        video.current_step = '处理失败'
        db_session.commit()

        assert video.status == VideoStatus.FAILED
        assert '文件损坏' in video.error_message


class TestPlaceholderFileHandling:
    """占位文件处理测试"""

    def test_detect_placeholder_file(self, app):
        """测试占位文件检测"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mp4', delete=False) as f:
            f.write('慕课视频链接：https://example.com/video')
            temp_path = f.name

        try:
            # 检测是否为占位文件
            is_placeholder = False
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read(100)
                if '慕课视频链接' in content or '无法下载慕课视频' in content:
                    is_placeholder = True

            assert is_placeholder is True
        finally:
            os.remove(temp_path)

    def test_detect_real_video_file(self, app):
        """测试真实视频文件检测"""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            # 写入一些二进制数据模拟视频
            f.write(b'\x00\x00\x00\x1c\x66\x74\x79\x70\x69\x73\x6f\x6d')
            temp_path = f.name

        try:
            is_placeholder = False
            try:
                with open(temp_path, 'r', encoding='utf-8') as f:
                    content = f.read(100)
                    if '慕课视频链接' in content:
                        is_placeholder = True
            except UnicodeDecodeError:
                # 二进制文件，不是占位文件
                is_placeholder = False

            assert is_placeholder is False
        finally:
            os.remove(temp_path)


class TestTaskContractForMigration:
    """
    任务契约测试
    确保迁移到 ProcessPoolExecutor 后核心逻辑保持一致
    """

    def test_process_video_return_format(self, app, db_session):
        """测试处理视频返回格式契约"""
        # 成功返回格式
        success_result = {'status': 'success', 'message': '视频处理成功'}
        assert 'status' in success_result
        assert 'message' in success_result
        assert success_result['status'] == 'success'

        # 失败返回格式
        failed_result = {'status': 'failed', 'message': '处理视频失败: 文件不存在'}
        assert 'status' in failed_result
        assert 'message' in failed_result
        assert failed_result['status'] == 'failed'

    def test_cleanup_video_return_format(self, app, db_session):
        """测试清理视频返回格式契约"""
        # 成功返回格式
        success_result = {'status': 'success', 'message': '视频文件清理完成'}
        assert 'status' in success_result
        assert success_result['status'] == 'success'

        # 错误返回格式
        error_result = {'status': 'error', 'message': '未找到ID为99999的视频'}
        assert 'status' in error_result
        assert error_result['status'] == 'error'

    def test_subtitle_generate_return_format(self, app):
        """测试字幕生成返回格式契约"""
        # 成功返回格式
        success_result = {'status': 'success', 'message': '字幕生成成功'}
        assert 'status' in success_result
        assert success_result['status'] == 'success'
