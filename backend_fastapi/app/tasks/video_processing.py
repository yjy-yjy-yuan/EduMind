"""
视频处理后台任务 - FastAPI 版本
使用 ProcessPoolExecutor 替代 Celery

主要功能：
1. 视频预览图生成
2. 视频信息提取
3. 字幕生成和格式化
4. 音频转录 (支持 CUDA/MPS/CPU)
"""

import gc
import logging
import os
import subprocess
import time

logger = logging.getLogger(__name__)


def get_device():
    """获取最佳计算设备 - 自动检测 CUDA/MPS/CPU"""
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            # 检测 PyTorch 版本，MPS 在 2.1+ 更稳定
            pytorch_version = torch.__version__.split("+")[0]
            major, minor = map(int, pytorch_version.split(".")[:2])
            if major > 2 or (major == 2 and minor >= 1):
                return "mps"
            logger.warning(f"PyTorch {pytorch_version} 的 MPS 不完全兼容，使用 CPU")
    except ImportError:
        pass
    return "cpu"


def clear_gpu_cache():
    """清理 GPU 缓存，释放显存"""
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("已清理 CUDA 缓存")
        elif hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
            torch.mps.empty_cache()
            logger.info("已清理 MPS 缓存")
    except Exception as e:
        logger.warning(f"清理 GPU 缓存时出错: {str(e)}")
    gc.collect()


def generate_video_info(video_path: str) -> dict:
    """获取视频信息"""
    try:
        import cv2

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频文件: {video_path}")
            return None

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        cap.release()

        return {"width": width, "height": height, "fps": fps, "frame_count": frame_count, "duration": duration}
    except Exception as e:
        logger.error(f"获取视频信息失败: {str(e)}")
        return None


def is_placeholder_file(filepath: str) -> bool:
    """检查是否为占位文件"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(100)
            return "慕课视频链接" in content or "无法下载慕课视频" in content
    except (UnicodeDecodeError, Exception):
        return False


def generate_preview_image(video_path: str, preview_path: str) -> bool:
    """生成视频预览图"""
    try:
        import cv2
        import numpy as np

        # 检查是否为占位文件
        if is_placeholder_file(video_path):
            img = np.zeros((360, 640, 3), dtype=np.uint8)
            img[:, :] = (25, 55, 125)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(img, "Placeholder Video", (160, 180), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(img, "Please replace manually", (140, 220), font, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.imwrite(preview_path, img)
            return True

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return False

        cv2.imwrite(preview_path, frame)
        return True
    except Exception as e:
        logger.error(f"生成预览图失败: {str(e)}")
        return False


def extract_audio(video_path: str, audio_path: str) -> bool:
    """从视频中提取音频"""
    try:
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-threads",
            "4",
            audio_path,
        ]

        process = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=300)
        return os.path.exists(audio_path)
    except Exception as e:
        logger.error(f"提取音频失败: {str(e)}")
        return False


def transcribe_with_whisper(audio_path: str, model_name: str, language: str, model_path: str) -> dict:
    """使用 Whisper 转录音频"""
    try:
        import whisper

        device = get_device()
        logger.info(f"加载 Whisper 模型: {model_name} (设备: {device})")

        # 加载模型
        model = whisper.load_model(model_name, device=device, download_root=model_path)

        # 转录
        logger.info(f"开始转录: {os.path.basename(audio_path)}")
        start_time = time.time()

        result = model.transcribe(
            audio_path,
            language=language if language else None,
            verbose=False,
            fp16=(device == "cuda"),
        )

        elapsed = time.time() - start_time
        logger.info(f"转录完成，耗时: {elapsed:.1f}秒")

        # 清理
        del model
        clear_gpu_cache()

        return result
    except Exception as e:
        logger.error(f"转录失败: {str(e)}")
        clear_gpu_cache()
        return None


def save_subtitles(result: dict, srt_path: str, txt_path: str):
    """保存字幕文件"""
    try:
        from whisper.utils import WriteSRT
        from whisper.utils import WriteTXT

        with open(srt_path, "w", encoding="utf-8") as srt:
            WriteSRT(None).write_result(result, srt)

        with open(txt_path, "w", encoding="utf-8") as txt:
            WriteTXT(None).write_result(result, txt)

        logger.info(f"字幕已保存: {os.path.basename(srt_path)}")
        return True
    except Exception as e:
        logger.error(f"保存字幕失败: {str(e)}")
        return False


def update_video_status(video_id: int, status: str, progress: float, step: str, **kwargs):
    """更新视频状态 (在子进程中创建新的数据库连接)"""
    # 动态导入以避免跨进程问题
    from app.core.config import settings
    from app.models.video import Video
    from app.models.video import VideoStatus
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    )
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.status = VideoStatus(status) if isinstance(status, str) else status
            video.process_progress = progress
            video.current_step = step

            for key, value in kwargs.items():
                if hasattr(video, key):
                    setattr(video, key, value)

            db.commit()
    finally:
        db.close()
        engine.dispose()


def process_video_task(video_id: int, language: str = "zh", model: str = "base"):
    """
    视频处理任务（在 ProcessPoolExecutor 中执行）

    Args:
        video_id: 视频ID
        language: 语言代码 (zh, en, ja 等)
        model: Whisper 模型名称 (tiny, base, small, medium, large, turbo)

    Returns:
        dict: 处理结果
    """
    logger.info(f"开始处理视频 | ID: {video_id} | 语言: {language} | 模型: {model}")

    # 动态导入以避免跨进程问题
    from app.core.config import settings
    from app.models.video import Video
    from app.models.video import VideoStatus
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    )
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 获取视频信息
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.error(f"视频不存在 | ID: {video_id}")
            return {"status": "failed", "message": "视频不存在"}

        video_path = video.filepath
        filename = video.filename

        # 更新状态为处理中
        video.status = VideoStatus.PROCESSING
        video.process_progress = 0.0
        video.current_step = "初始化处理"
        db.commit()

        # 检查是否为占位文件
        is_placeholder = is_placeholder_file(video_path)

        if is_placeholder:
            logger.warning(f"检测到占位文件: {video_path}")
            video.process_progress = 50.0
            video.current_step = "处理占位文件"
            db.commit()

        # Step 1: 生成预览图 (10%)
        video.process_progress = 10.0
        video.current_step = "生成预览图"
        db.commit()

        preview_dir = os.path.join(settings.UPLOAD_FOLDER, "previews")
        os.makedirs(preview_dir, exist_ok=True)
        preview_filename = f"preview_{video_id}.jpg"
        preview_path = os.path.join(preview_dir, preview_filename)

        if generate_preview_image(video_path, preview_path):
            video.preview_filename = preview_filename
            video.preview_filepath = preview_path
            db.commit()
        else:
            if not is_placeholder:
                video.status = VideoStatus.FAILED
                video.current_step = "生成预览图失败"
                db.commit()
                return {"status": "failed", "message": "生成预览图失败"}

        # Step 2: 提取视频信息 (30%)
        video.process_progress = 30.0
        video.current_step = "提取视频信息"
        db.commit()

        if is_placeholder:
            video.duration = 0
            video.fps = 0
            video.width = 640
            video.height = 360
            video.frame_count = 0
        else:
            video_info = generate_video_info(video_path)
            if video_info:
                video.width = video_info["width"]
                video.height = video_info["height"]
                video.fps = video_info["fps"]
                video.frame_count = video_info["frame_count"]
                video.duration = video_info["duration"]
            else:
                video.status = VideoStatus.FAILED
                video.current_step = "获取视频信息失败"
                db.commit()
                return {"status": "failed", "message": "获取视频信息失败"}

        db.commit()

        # 如果是占位文件，直接完成
        if is_placeholder:
            video.status = VideoStatus.COMPLETED
            video.processed = True
            video.process_progress = 100.0
            video.current_step = "完成"
            db.commit()
            return {"status": "success", "message": "占位文件处理完成"}

        # Step 3: 提取音频 (50%)
        video.process_progress = 50.0
        video.current_step = "提取音频"
        db.commit()

        audio_dir = os.path.join(settings.UPLOAD_FOLDER, "audio_temp")
        os.makedirs(audio_dir, exist_ok=True)
        base_filename = os.path.splitext(os.path.basename(video_path))[0]
        audio_path = os.path.join(audio_dir, f"{base_filename}.wav")

        input_file = video_path
        if extract_audio(video_path, audio_path):
            input_file = audio_path
            logger.info("音频提取成功")
        else:
            logger.warning("音频提取失败，使用原视频文件")

        # Step 4: 转录 (60-85%)
        video.process_progress = 60.0
        video.current_step = f"加载 {model} 模型"
        db.commit()

        result = transcribe_with_whisper(input_file, model, language, settings.WHISPER_MODEL_PATH)

        if not result:
            video.status = VideoStatus.FAILED
            video.current_step = "转录失败"
            db.commit()
            return {"status": "failed", "message": "转录失败"}

        # Step 5: 保存字幕 (85-95%)
        video.process_progress = 85.0
        video.current_step = "生成字幕文件"
        db.commit()

        subtitle_dir = os.path.join(settings.UPLOAD_FOLDER, "subtitles")
        os.makedirs(subtitle_dir, exist_ok=True)
        srt_path = os.path.join(subtitle_dir, f"{base_filename}.srt")
        txt_path = os.path.join(subtitle_dir, f"{base_filename}.txt")

        if save_subtitles(result, srt_path, txt_path):
            video.subtitle_filepath = srt_path
        else:
            logger.warning("保存字幕失败，但继续完成处理")

        # 清理临时音频文件
        if input_file != video_path and os.path.exists(input_file):
            try:
                os.remove(input_file)
            except Exception:
                pass

        # 完成
        video.status = VideoStatus.COMPLETED
        video.processed = True
        video.process_progress = 100.0
        video.current_step = "处理完成"
        db.commit()

        logger.info(f"视频处理完成 | ID: {video_id}")
        return {"status": "success", "message": "视频处理成功"}

    except Exception as e:
        logger.error(f"处理视频失败 | ID: {video_id} | 错误: {str(e)}")

        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = VideoStatus.FAILED
                video.process_progress = 0.0
                video.current_step = f"处理失败: {str(e)}"
                db.commit()
        except Exception:
            pass

        clear_gpu_cache()
        return {"status": "failed", "message": f"处理视频失败: {str(e)}"}

    finally:
        db.close()
        engine.dispose()


def cleanup_video_task(video_id: int) -> dict:
    """
    清理视频文件任务

    Args:
        video_id: 视频ID

    Returns:
        dict: 清理结果
    """
    logger.info(f"开始清理视频 | ID: {video_id}")

    from app.core.config import settings
    from app.models.qa import Question
    from app.models.video import Video
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    )
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {"status": "error", "message": f"未找到ID为{video_id}的视频"}

        # 删除关联的问题记录
        db.query(Question).filter(Question.video_id == video_id).delete()

        # 删除文件
        files_to_delete = [
            video.filepath,
            video.processed_filepath,
            video.preview_filepath,
            video.subtitle_filepath,
        ]

        for filepath in files_to_delete:
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    logger.warning(f"删除文件失败: {filepath} - {str(e)}")

        # 删除数据库记录
        db.delete(video)
        db.commit()

        logger.info(f"视频清理完成 | ID: {video_id}")
        return {"status": "success", "message": "视频文件清理完成"}

    except Exception as e:
        logger.error(f"清理视频文件时出错: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()
        engine.dispose()
