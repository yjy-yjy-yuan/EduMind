from app import create_app
from app.models import Subtitle

def check_subtitles():
    app = create_app()
    with app.app_context():
        total_count = Subtitle.query.count()
        video1_count = Subtitle.query.filter_by(video_id=1).count()
        
        print(f'字幕总数: {total_count}')
        print(f'视频1的字幕数: {video1_count}')
        
        if video1_count > 0:
            print("\n视频1的前5条字幕:")
            subtitles = Subtitle.query.filter_by(video_id=1).limit(5).all()
            for sub in subtitles:
                print(f"ID: {sub.id}, 开始时间: {sub.start_time}, 结束时间: {sub.end_time}, 文本: {sub.text[:30]}...")

if __name__ == '__main__':
    check_subtitles()
