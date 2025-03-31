from datetime import datetime
from app.extensions import db

class Note(db.Model):
    """笔记模型"""
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)  # 纯文本内容
    content_vector = db.Column(db.Text, nullable=True)  # 内容向量（JSON格式存储）
    note_type = db.Column(db.String(50), default='text')  # 笔记类型：text, code, list等
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = db.Column(db.String(255), nullable=True)  # 存储标签，以逗号分隔
    keywords = db.Column(db.String(500), nullable=True)  # 自动提取的关键词

    # 关系
    video = db.relationship('Video', backref=db.backref('notes', lazy='dynamic'))
    timestamps = db.relationship('NoteTimestamp', backref='note', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """将笔记转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'note_type': self.note_type,
            'video_id': self.video_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags.split(',') if self.tags else [],
            'keywords': self.keywords.split(',') if self.keywords else [],
            'timestamps': [ts.to_dict() for ts in self.timestamps]
        }

class NoteTimestamp(db.Model):
    """笔记时间戳模型，用于关联笔记与视频的特定时间点"""
    __tablename__ = 'note_timestamps'

    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    time_seconds = db.Column(db.Float, nullable=False)  # 视频时间点（秒）
    subtitle_text = db.Column(db.Text, nullable=True)  # 对应的字幕文本
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """将时间戳转换为字典"""
        return {
            'id': self.id,
            'note_id': self.note_id,
            'time_seconds': self.time_seconds,
            'subtitle_text': self.subtitle_text,
            'created_at': self.created_at.isoformat()
        }
