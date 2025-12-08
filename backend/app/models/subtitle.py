from datetime import datetime

from ..extensions import db


class Subtitle(db.Model):
    __tablename__ = 'subtitles'

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)

    # 字幕时间信息
    start_time = db.Column(db.Float, nullable=False)  # 开始时间（秒）
    end_time = db.Column(db.Float, nullable=False)  # 结束时间（秒）

    # 字幕内容
    text = db.Column(db.Text, nullable=False)  # 字幕文本

    # 字幕来源和类型
    source = db.Column(
        db.String(50), nullable=False
    )  # 来源：'asr'（语音识别）, 'extract'（视频提取）, 'manual'（手动添加）
    language = db.Column(db.String(10), nullable=False, default='zh')  # 语言代码：'zh', 'en'等

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    video = db.relationship('Video', back_populates='subtitles')

    def __repr__(self):
        return f'<Subtitle {self.id} for Video {self.video_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'text': self.text,
            'source': self.source,
            'language': self.language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def format_time(seconds):
        """将秒数转换为 SRT 格式的时间字符串 (MM:SS)"""
        minutes = int(float(seconds) // 60)
        seconds = int(float(seconds) % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def to_srt(self, index):
        """将字幕转换为 SRT 格式"""
        start_mm = int(float(self.start_time) // 60)
        start_ss = int(float(self.start_time) % 60)
        end_mm = int(float(self.end_time) // 60)
        end_ss = int(float(self.end_time) % 60)

        return f"{index}\n{start_mm:02d}:{start_ss:02d} - {end_mm:02d}:{end_ss:02d}\n{self.text}\n"
