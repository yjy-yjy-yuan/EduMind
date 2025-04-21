from app import create_app
from app.models.video import Video
from app.models.subtitle import Subtitle

app = create_app()
with app.app_context():
    # 获取视频信息
    video = Video.query.get(1)
    if video:
        print(f"视频ID: 1")
        print(f"标题: {video.title or video.filename}")
        print(f"状态: {video.status}")
        
        # 获取字幕信息
        subtitles = Subtitle.query.filter_by(video_id=1).all()
        print(f"字幕数量: {len(subtitles)}")
        
        # 如果有字幕，打印前3条
        if subtitles:
            print("前3条字幕内容:")
            for i, subtitle in enumerate(subtitles[:3]):
                print(f"  {i+1}. {subtitle.text[:50]}...")
        else:
            print("该视频没有字幕数据")
    else:
        print("视频ID=1的视频不存在")
