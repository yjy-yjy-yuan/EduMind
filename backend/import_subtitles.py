import json
import os
from app import create_app
from app.models.video import Video
from app.models.subtitle import Subtitle
from app.extensions import db

def import_subtitles_for_video(video_id, subtitle_file_path):
    """
    从字幕文件导入字幕数据到数据库
    
    :param video_id: 视频ID
    :param subtitle_file_path: 字幕文件路径（JSON格式）
    :return: 成功时返回True，否则返回False
    """
    try:
        # 读取JSON字幕文件
        with open(subtitle_file_path, 'r', encoding='utf-8') as f:
            subtitle_data = json.load(f)
        
        # 检查字幕数据格式
        segments = None
        
        # 如果是字典格式，尝试获取segments字段
        if isinstance(subtitle_data, dict) and 'segments' in subtitle_data:
            segments = subtitle_data['segments']
            print(f"从字幕文件中找到 {len(segments)} 条字幕段")
        # 如果是数组格式，直接使用
        elif isinstance(subtitle_data, list):
            segments = subtitle_data
            print(f"从字幕文件中找到 {len(segments)} 条字幕")
        else:
            print(f"错误：字幕文件 {subtitle_file_path} 格式不支持")
            return False
        
        # 删除该视频的所有现有字幕
        existing_subtitles = Subtitle.query.filter_by(video_id=video_id).all()
        if existing_subtitles:
            print(f"删除视频ID {video_id} 的 {len(existing_subtitles)} 条现有字幕")
            for subtitle in existing_subtitles:
                db.session.delete(subtitle)
            db.session.commit()
        
        # 导入新字幕
        subtitle_count = 0
        for item in segments:
            # 检查必要字段
            start = item.get('start') or item.get('start_time')
            end = item.get('end') or item.get('end_time')
            text = item.get('text')
            
            if not start or not end or not text:
                continue
            
            # 如果是字符串，转换为浮点数
            if isinstance(start, str):
                start = float(start)
            if isinstance(end, str):
                end = float(end)
            
            # 创建字幕记录
            subtitle = Subtitle(
                video_id=video_id,
                start_time=start,
                end_time=end,
                text=text,
                source='extract',  # 假设来源是从视频中提取
                language='zh'      # 假设语言是中文
            )
            db.session.add(subtitle)
            subtitle_count += 1
        
        # 提交事务
        db.session.commit()
        print(f"成功为视频ID {video_id} 导入 {subtitle_count} 条字幕")
        return True
        
    except Exception as e:
        print(f"导入字幕时出错: {str(e)}")
        db.session.rollback()
        return False

def main():
    app = create_app()
    with app.app_context():
        # 获取视频信息
        video = Video.query.get(1)
        if not video:
            print("视频ID=1的视频不存在")
            return
        
        print(f"视频ID: 1")
        print(f"标题: {video.title or video.filename}")
        print(f"状态: {video.status}")
        
        # 构建字幕文件路径
        video_filename = video.title or video.filename
        
        # 直接使用完整文件名
        subtitle_file_path = os.path.join(
            'backend', 'uploads', 'subtitles', f"{video_filename}.json"
        )
        
        # 如果文件不存在，尝试使用相对路径
        if not os.path.exists(subtitle_file_path):
            subtitle_file_path = os.path.join(
                'uploads', 'subtitles', f"{video_filename}.json"
            )
        
        # 检查字幕文件是否存在
        if not os.path.exists(subtitle_file_path):
            print(f"字幕文件不存在: {subtitle_file_path}")
            return
        
        print(f"找到字幕文件: {subtitle_file_path}")
        
        # 导入字幕
        if import_subtitles_for_video(1, subtitle_file_path):
            print("字幕导入成功")
            
            # 验证导入结果
            subtitles = Subtitle.query.filter_by(video_id=1).all()
            print(f"导入后字幕数量: {len(subtitles)}")
            
            # 如果有字幕，打印前3条
            if subtitles:
                print("前3条字幕内容:")
                for i, subtitle in enumerate(subtitles[:3]):
                    print(f"  {i+1}. {subtitle.text[:50]}...")
        else:
            print("字幕导入失败")

if __name__ == "__main__":
    main()
