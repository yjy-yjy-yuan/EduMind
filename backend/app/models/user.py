"""用户模型"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # 扩展个人信息字段
    gender = db.Column(db.String(10), nullable=True)  # 性别
    education = db.Column(db.String(50), nullable=True)  # 学历
    occupation = db.Column(db.String(50), nullable=True)  # 职业
    learning_direction = db.Column(db.String(100), nullable=True)  # 学习方向
    avatar = db.Column(db.String(255), nullable=True)  # 头像URL
    bio = db.Column(db.Text, nullable=True)  # 个人简介
    
    def __init__(self, username, email, password, gender=None, education=None, 
                 occupation=None, learning_direction=None, avatar=None, bio=None):
        self.username = username
        self.email = email
        self.set_password(password)
        self.gender = gender
        self.education = education
        self.occupation = occupation
        self.learning_direction = learning_direction
        self.avatar = avatar
        self.bio = bio
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'gender': self.gender,
            'education': self.education,
            'occupation': self.occupation,
            'learning_direction': self.learning_direction,
            'avatar': self.avatar,
            'bio': self.bio,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'
