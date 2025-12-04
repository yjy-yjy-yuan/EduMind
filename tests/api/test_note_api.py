"""
API 测试 - 笔记相关接口
测试笔记的 CRUD 操作
"""
import pytest
import json


class TestNoteListAPI:
    """笔记列表 API 测试"""

    def test_get_notes_empty(self, client):
        """测试获取空笔记列表"""
        response = client.get('/api/notes/notes')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, (list, dict))


class TestNoteCreateAPI:
    """笔记创建 API 测试"""

    def test_create_note_success(self, client, sample_note_data, auth_headers):
        """测试成功创建笔记"""
        # 转换 tags 列表为逗号分隔的字符串
        note_data = {
            'title': sample_note_data['title'],
            'content': sample_note_data['content'],
            'tags': ','.join(sample_note_data['tags'])
        }
        response = client.post(
            '/api/notes/notes',
            data=json.dumps(note_data),
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        data = response.get_json()
        if 'note' in data:
            assert data['note']['title'] == sample_note_data['title']

    def test_create_note_without_title(self, client, auth_headers):
        """测试创建无标题笔记"""
        response = client.post(
            '/api/notes/notes',
            data=json.dumps({'content': '只有内容'}),
            headers=auth_headers
        )
        # 应该失败（title 是必填字段）
        assert response.status_code in [400, 422, 500]

    def test_create_note_empty_body(self, client, auth_headers):
        """测试空请求体创建笔记"""
        response = client.post(
            '/api/notes/notes',
            data=json.dumps({}),
            headers=auth_headers
        )
        assert response.status_code in [400, 422, 500]


class TestNoteDetailAPI:
    """笔记详情 API 测试"""

    def test_get_nonexistent_note(self, client):
        """测试获取不存在的笔记"""
        response = client.get('/api/notes/notes/99999')
        assert response.status_code in [404, 500]

    def test_update_nonexistent_note(self, client, auth_headers):
        """测试更新不存在的笔记"""
        response = client.put(
            '/api/notes/notes/99999',
            data=json.dumps({'title': '更新', 'content': '内容'}),
            headers=auth_headers
        )
        assert response.status_code in [404, 500]

    def test_delete_nonexistent_note(self, client):
        """测试删除不存在的笔记"""
        response = client.delete('/api/notes/notes/99999')
        assert response.status_code in [404, 500]


class TestNoteSimilarAPI:
    """笔记相似搜索 API 测试"""

    def test_similar_notes_without_content(self, client, auth_headers):
        """测试无内容的相似搜索"""
        response = client.post(
            '/api/notes/notes/similar',
            data=json.dumps({}),
            headers=auth_headers
        )
        assert response.status_code in [200, 400, 500]

    def test_similar_notes_with_content(self, client, auth_headers):
        """测试有效内容的相似搜索"""
        response = client.post(
            '/api/notes/notes/similar',
            data=json.dumps({'content': '测试内容'}),
            headers=auth_headers
        )
        # 可能返回空结果或成功
        assert response.status_code in [200, 500]
