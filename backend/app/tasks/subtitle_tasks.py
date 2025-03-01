from .. import db, celery
from ..models import Video, Subtitle
import whisper
import logging
import os

@celery.task(name='app.tasks.subtitle_tasks.generate_subtitles')
def generate_subtitles(video_id, language='zh', model_name='base'):
    """生成视频字幕的Celery任务"""
    try:
        logging.info(f"开始生成字幕任务: video_id={video_id}, language={language}, model_name={model_name}")
        
        # 获取视频信息
        video = Video.query.get(video_id)
        if not video:
            raise Exception(f"视频不存在: {video_id}")
            
        logging.info(f"开始处理视频: {video.title}")
        
        # 获取视频文件路径
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        video_path = os.path.join(base_dir, 'uploads', f"{video.title}_{video.id}_processed.mp4")
        if not os.path.exists(video_path):
            raise Exception(f"视频文件不存在: {video_path}")
            
        # 加载Whisper模型
        logging.info(f"正在加载Whisper模型: {model_name}")
        model = whisper.load_model(model_name)
        
        # 开始转写
        logging.info("开始转写音频...")
        result = model.transcribe(video_path, language=language)
        
        # 保存字幕
        logging.info("正在保存字幕...")
        try:
            # 删除已有的字幕
            Subtitle.query.filter_by(video_id=video_id).delete()
            
            # 添加新的字幕
            for segment in result["segments"]:
                subtitle = Subtitle(
                    video_id=video_id,
                    start_time=round(segment["start"]),
                    end_time=round(segment["end"]),
                    text=segment["text"],
                    language=language
                )
                db.session.add(subtitle)
                
            db.session.commit()
            return {
                'status': 'success',
                'message': '字幕生成成功'
            }
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"保存字幕时发生错误: {str(e)}"
            logging.error(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        error_msg = f"字幕生成失败: {str(e)}"
        logging.error(error_msg)
        raise Exception(error_msg)
