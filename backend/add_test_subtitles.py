from app import create_app
from app.models import Subtitle, db
import datetime

def add_test_subtitles():
    app = create_app()
    with app.app_context():
        # 检查是否已经有数据
        existing_count = Subtitle.query.filter_by(video_id=1).count()
        if existing_count > 0:
            print(f"视频1已有{existing_count}条字幕，不再添加测试数据")
            return
        
        # 添加测试字幕数据
        test_subtitles = [
            {"video_id": 1, "start_time": 5.0, "end_time": 10.0, "text": "欢迎来到这个教学视频", "source": "test", "language": "zh-CN"},
            {"video_id": 1, "start_time": 12.0, "end_time": 18.0, "text": "今天我们将学习如何使用人工智能进行数据分析", "source": "test", "language": "zh-CN"},
            {"video_id": 1, "start_time": 20.0, "end_time": 25.0, "text": "首先，我们需要了解什么是机器学习", "source": "test", "language": "zh-CN"},
            {"video_id": 1, "start_time": 27.0, "end_time": 35.0, "text": "机器学习是人工智能的一个分支，它使用算法和统计模型来分析数据", "source": "test", "language": "zh-CN"},
            {"video_id": 1, "start_time": 37.0, "end_time": 45.0, "text": "通过机器学习，计算机可以从数据中学习并做出预测或决策", "source": "test", "language": "zh-CN"},
            {"video_id": 1, "start_time": 47.0, "end_time": 55.0, "text": "常见的机器学习算法包括线性回归、决策树和神经网络", "source": "test", "language": "zh-CN"},
            {"video_id": 1, "start_time": 57.0, "end_time": 65.0, "text": "在数据分析中，我们首先需要收集和清洗数据", "source": "test", "language": "zh-CN"},
            {"video_id": 1, "start_time": 67.0, "end_time": 75.0, "text": "然后，我们可以使用机器学习算法来分析这些数据", "source": "test", "language": "zh-CN"},
            {"video_id": 1, "start_time": 77.0, "end_time": 85.0, "text": "最后，我们根据分析结果做出决策或预测", "source": "test", "language": "zh-CN"},
            {"video_id": 1, "start_time": 87.0, "end_time": 95.0, "text": "希望这个视频对你有所帮助，谢谢观看", "source": "test", "language": "zh-CN"}
        ]
        
        now = datetime.datetime.utcnow()
        
        for sub_data in test_subtitles:
            subtitle = Subtitle(
                video_id=sub_data["video_id"],
                start_time=sub_data["start_time"],
                end_time=sub_data["end_time"],
                text=sub_data["text"],
                source=sub_data["source"],
                language=sub_data["language"],
                created_at=now,
                updated_at=now
            )
            db.session.add(subtitle)
        
        db.session.commit()
        print(f"成功添加了{len(test_subtitles)}条测试字幕")

if __name__ == '__main__':
    add_test_subtitles()
