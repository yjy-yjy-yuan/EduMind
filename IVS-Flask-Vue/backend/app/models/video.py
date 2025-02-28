"""视频模型"""
from datetime import datetime
from ..extensions import db
from enum import Enum

class VideoStatus(Enum):
    """视频状态枚举"""
    UPLOADED = 'uploaded'   # 已上传
    PENDING = 'pending'     # 等待处理
    PROCESSING = 'processing'  # 处理中
    COMPLETED = 'completed'    # 处理完成
    FAILED = 'failed'         # 处理失败
    DOWNLOADING = 'downloading'  # 下载中（用于视频链接上传）

class Video(db.Model):
    """视频模型"""
    __tablename__ = 'videos'
    
    # 基本信息
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    filename = db.Column(db.String(255), nullable=True)
    filepath = db.Column(db.String(255), nullable=True)
    processed_filename = db.Column(db.String(255), nullable=True)
    processed_filepath = db.Column(db.String(255), nullable=True)
    preview_filename = db.Column(db.String(255), nullable=True)
    preview_filepath = db.Column(db.String(255), nullable=True)
    subtitle_filepath = db.Column(db.String(255), nullable=True)
    url = db.Column(db.String(255), nullable=True)
    
    # 状态信息
    status = db.Column(db.Enum(VideoStatus), default=VideoStatus.UPLOADED)
    error_message = db.Column(db.Text, nullable=True)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 视频属性
    duration = db.Column(db.Float, nullable=True)      # 视频时长（秒）
    fps = db.Column(db.Float, nullable=True)          # 帧率
    width = db.Column(db.Integer, nullable=True)      # 视频宽度
    height = db.Column(db.Integer, nullable=True)     # 视频高度
    frame_count = db.Column(db.Integer, nullable=True) # 总帧数
    
    # 字幕关联
    subtitles = db.relationship('Subtitle', back_populates='video', lazy=True)
    
    def __repr__(self):
        return f'<Video {self.title or self.filename}>'
        
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'filename': self.filename,
            'processed_filename': self.processed_filename,
            'preview_filename': self.preview_filename,
            'status': self.status.value,
            'error_message': self.error_message,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'duration': self.duration,
            'fps': self.fps,
            'width': self.width,
            'height': self.height,
            'frame_count': self.frame_count
        }
