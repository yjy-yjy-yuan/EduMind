"""学习流智能体 API 测试。"""

import pytest
from app.models.note import Note
from app.models.qa import Question
from app.models.subtitle import Subtitle
from app.models.video import VideoStatus


@pytest.mark.api
def test_execute_agent_creates_note_and_timestamp(client, db, sample_video):
    sample_video.status = VideoStatus.COMPLETED
    sample_video.summary = "视频摘要"
    db.add(
        Subtitle(
            video_id=sample_video.id,
            start_time=240.0,
            end_time=255.0,
            text="这一段讲的是导数的几何意义。",
            source="asr",
            language="zh",
        )
    )
    db.commit()

    response = client.post(
        "/api/agent/execute",
        json={
            "video_id": sample_video.id,
            "page_context": "video_detail",
            "current_time_seconds": 245,
            "subtitle_text": "这一段讲的是导数的几何意义。",
            "recent_qa_messages": [],
            "user_input": "把这一段记成笔记并总结一下",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] in {"create_note", "mixed"}
    assert "note_created" in payload["actions"]
    assert payload["result"]["note_id"]

    note = db.query(Note).filter(Note.id == payload["result"]["note_id"]).first()
    assert note is not None
    assert note.video_id == sample_video.id
    assert db.query(Question).count() == 0


@pytest.mark.api
def test_execute_agent_rejects_missing_video(client):
    response = client.post(
        "/api/agent/execute",
        json={
            "video_id": 9999,
            "page_context": "qa",
            "current_time_seconds": 12,
            "subtitle_text": "字幕",
            "recent_qa_messages": [],
            "user_input": "保存为笔记",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "视频不存在"
