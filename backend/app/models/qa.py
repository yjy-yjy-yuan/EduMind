from datetime import datetime

from app import db


class Question(db.Model):
    """问题模型"""

    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=True)  # 允许为NULL，以支持自由问答模式
    content = db.Column(db.Text, nullable=False)  # 问题内容
    answer = db.Column(db.Text)  # 回答内容
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联字段
    video = db.relationship('Video', backref=db.backref('questions', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'content': self.content,
            'answer': self.answer,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
