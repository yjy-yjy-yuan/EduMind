from .. import db, celery
from ..models import Video, Subtitle
import whisper
import logging
import os
from tqdm import tqdm
import opencc  # 导入OpenCC用于繁简转换

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
        with tqdm(total=1, desc="加载模型", unit="模型", ncols=100) as pbar:
            model = whisper.load_model(model_name)
            pbar.update(1)
        
        # 开始转写
        logging.info("开始转写音频...")
        # 使用自定义回调函数来更新进度条
        class ProgressCallback:
            def __init__(self):
                self.pbar = tqdm(total=100, desc="转写音频", unit="%", ncols=100)
                self.last_progress = 0
                
            def __call__(self, progress):
                # progress是0到1之间的值
                current_progress = int(progress * 100)
                update_amount = current_progress - self.last_progress
                if update_amount > 0:
                    self.pbar.update(update_amount)
                    self.last_progress = current_progress
                    
            def close(self):
                self.pbar.close()
                
        progress_callback = ProgressCallback()
        result = model.transcribe(video_path, language=language, verbose=True, progress_callback=progress_callback)
        progress_callback.close()
        
        # 初始化繁体到简体的转换器
        converter = opencc.OpenCC('t2s')
        
        # 保存字幕
        logging.info("正在保存字幕...")
        try:
            # 删除已有的字幕
            Subtitle.query.filter_by(video_id=video_id).delete()
            
            # 添加新的字幕
            with tqdm(total=len(result["segments"]), desc="保存字幕", unit="段", ncols=100) as pbar:
                for segment in result["segments"]:
                    # 将可能的繁体字幕转换为简体
                    simplified_text = converter.convert(segment["text"])
                    
                    subtitle = Subtitle(
                        video_id=video_id,
                        start_time=round(segment["start"]),
                        end_time=round(segment["end"]),
                        text=simplified_text,  # 使用转换后的简体文本
                        language=language
                    )
                    db.session.add(subtitle)
                    pbar.update(1)
                
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
