"""站外候选元数据服务单测。"""

import json

from app.services import external_candidate_service as service


class FakeResponse:
    """最小响应对象。"""

    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise service.requests.HTTPError(f"status={self.status_code}")


def test_bilibili_adapter_parses_search_results(monkeypatch):
    """B 站适配器应能提取标题、作者与链接。"""
    html = """
    <a href="//www.bilibili.com/video/BV1abc123/"></a>
    <h3 class="bili-video-card__info--tit" title="导数与函数单调性综合串讲"></h3>
    <span class="bili-video-card__info--author">宋老师</span>
    <span class="bili-video-card__info--date"> · 2025-03-01</span>
    """

    monkeypatch.setattr(service.requests, "get", lambda *args, **kwargs: FakeResponse(html))

    adapter = service.BilibiliExternalCandidateAdapter()
    items = adapter.search("数学 导数", subject_hint="数学", preferred_tags=["导数"], limit=1)

    assert len(items) == 1
    assert items[0].source_label == "B站"
    assert items[0].title == "导数与函数单调性综合串讲"
    assert items[0].external_url == "https://www.bilibili.com/video/BV1abc123"
    assert items[0].subject == "数学"
    assert items[0].tags[0] == "数学"


def test_youtube_adapter_parses_yt_initial_data(monkeypatch):
    """YouTube 适配器应能从 ytInitialData 中提取视频信息。"""
    payload = {
        "contents": {
            "twoColumnSearchResultsRenderer": {
                "primaryContents": {
                    "sectionListRenderer": {
                        "contents": [
                            {
                                "itemSectionRenderer": {
                                    "contents": [
                                        {
                                            "videoRenderer": {
                                                "videoId": "abc123xyz",
                                                "title": {"runs": [{"text": "Python Data Structures Crash Review"}]},
                                                "ownerText": {"runs": [{"text": "Computer Teacher"}]},
                                                "descriptionSnippet": {
                                                    "runs": [{"text": "Quick review for list and dict."}]
                                                },
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        }
    }
    html = f"<script>var ytInitialData = {json.dumps(payload)};</script>"

    monkeypatch.setattr(service.requests, "get", lambda *args, **kwargs: FakeResponse(html))

    adapter = service.YouTubeExternalCandidateAdapter()
    items = adapter.search("计算机 Python", subject_hint="计算机", preferred_tags=["Python"], limit=1)

    assert len(items) == 1
    assert items[0].source_label == "YouTube"
    assert items[0].external_url == "https://www.youtube.com/watch?v=abc123xyz"
    assert items[0].author == "Computer Teacher"
    assert items[0].subject == "计算机"
    assert items[0].tags[0] == "计算机"


def test_fetch_external_candidates_isolates_provider_failures(monkeypatch):
    """单个 provider 失败时，不应阻断其他站外候选返回。"""

    class BrokenAdapter(service.ExternalCandidateAdapter):
        provider = "broken"
        source_label = "坏源"

        def search(self, *args, **kwargs):
            raise service.requests.RequestException("boom")

    class GoodAdapter(service.ExternalCandidateAdapter):
        provider = "good"
        source_label = "好源"

        def search(self, *args, **kwargs):
            return [
                self.build_candidate(
                    raw_id="good-1",
                    title="中国大学慕课 · 数学相关课程",
                    external_url="https://www.icourse163.org/search.htm?search=%E6%95%B0%E5%AD%A6",
                    summary="打开中国大学慕课搜索页继续学习。",
                    tags=["数学", "导数"],
                    subject_hint="数学",
                )
            ]

    monkeypatch.setattr(service, "EXTERNAL_CANDIDATE_ADAPTERS", (BrokenAdapter(), GoodAdapter()))

    items = service.fetch_external_candidates("数学 导数", subject_hint="数学", preferred_tags=["导数"], limit=2)

    assert len(items) == 1
    assert items[0].source_label == "好源"
    assert items[0].subject == "数学"
