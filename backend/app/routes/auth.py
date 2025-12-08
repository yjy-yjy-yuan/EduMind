"""用户认证相关路由"""

from datetime import datetime

from app.extensions import db
from app.models.user import User
from flask import Blueprint
from flask import jsonify
from flask import request
from flask import session

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()

    # 验证请求数据
    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'success': False, 'message': '请提供用户名、邮箱和密码'}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'success': False, 'message': '用户名已存在'}), 400

    # 检查邮箱是否已存在
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'message': '邮箱已存在'}), 400

    # 创建新用户
    try:
        # 使用新的用户模型，包含扩展字段
        user = User(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            gender=data.get('gender'),
            education=data.get('education'),
            occupation=data.get('occupation'),
            learning_direction=data.get('learning_direction'),
            bio=data.get('bio'),
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({'success': True, 'message': '注册成功', 'user': user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()

    # 验证请求数据
    if not data or not all(k in data for k in ('username', 'password')):
        return jsonify({'success': False, 'message': '请提供用户名/邮箱和密码'}), 400

    # 查找用户（支持用户名或邮箱登录）
    user = User.query.filter_by(username=data['username']).first()
    if not user:
        # 尝试使用邮箱登录
        user = User.query.filter_by(email=data['username']).first()

    # 验证用户和密码
    if user and user.check_password(data['password']):
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()

        # 设置会话
        session['user_id'] = user.id

        return jsonify({'success': True, 'message': '登录成功', 'user': user.to_dict()}), 200

    return jsonify({'success': False, 'message': '用户名/邮箱或密码错误'}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用户退出登录"""
    session.pop('user_id', None)
    return jsonify({'success': True, 'message': '退出成功'}), 200


@auth_bp.route('/user', methods=['GET'])
def get_user():
    """获取当前登录用户信息"""
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': '未登录'}), 401

    user = User.query.get(user_id)

    if not user:
        session.pop('user_id', None)
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    return jsonify({'success': True, 'user': user.to_dict()}), 200


@auth_bp.route('/user/update', methods=['POST'])
def update_user():
    """更新用户信息"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.get_json()
    user = User.query.get(session['user_id'])

    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404

    # 更新用户信息
    if 'username' in data and data['username'] != user.username:
        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        user.username = data['username']

    if 'email' in data and data['email'] != user.email:
        # 检查邮箱是否已存在
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': '邮箱已存在'}), 400
        user.email = data['email']

    # 更新新增的个人信息字段
    if 'gender' in data:
        user.gender = data['gender']

    if 'education' in data:
        user.education = data['education']

    if 'occupation' in data:
        user.occupation = data['occupation']

    if 'learning_direction' in data:
        user.learning_direction = data['learning_direction']

    if 'bio' in data:
        user.bio = data['bio']

    if 'avatar' in data:
        user.avatar = data['avatar']

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': '更新成功', 'user': user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500
