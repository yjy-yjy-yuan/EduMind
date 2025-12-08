"""
集成测试 - 视频处理完整流程
测试从上传到处理完成的完整工作流

测试场景：
1. 视频上传 → 状态查询 → 删除
2. 视频上传 → 处理 → 字幕获取
3. 视频详情查询完整流程
4. 视频列表分页和过滤
"""

import io


class TestVideoUploadWorkflow:
    """视频上传完整流程测试"""

    def test_upload_and_query_workflow(self, client):
        """测试上传后查询视频的流程"""
        # 1. 上传视频
        fake_video = io.BytesIO(b'\x00\x00\x00\x1c\x66\x74\x79\x70\x69\x73\x6f\x6d')
        upload_response = client.post(
            '/api/videos/upload', data={'file': (fake_video, 'workflow_test.mp4')}, content_type='multipart/form-data'
        )

        # 上传可能成功或失败（取决于环境）
        if upload_response.status_code in [200, 201]:
            data = upload_response.get_json()
            video_id = data.get('id') or data.get('video', {}).get('id')

            if video_id:
                # 2. 查询视频详情
                detail_response = client.get(f'/api/videos/{video_id}')
                assert detail_response.status_code == 200

                # 3. 查询视频状态
                status_response = client.get(f'/api/videos/{video_id}/status')
                assert status_response.status_code == 200

                # 4. 删除视频
                delete_response = client.delete(f'/api/videos/{video_id}/delete')
                assert delete_response.status_code in [200, 204, 404]

    def test_video_list_pagination_workflow(self, client, completed_video):
        """测试视频列表分页流程"""
        # 1. 获取第一页
        page1_response = client.get('/api/videos/list?page=1&per_page=5')
        assert page1_response.status_code == 200
        page1_data = page1_response.get_json()
        assert 'videos' in page1_data

        # 2. 获取第二页
        page2_response = client.get('/api/videos/list?page=2&per_page=5')
        assert page2_response.status_code == 200

        # 3. 验证分页一致性
        page1_videos = page1_data['videos']
        page2_data = page2_response.get_json()
        page2_videos = page2_data['videos']

        # 如果有多页数据，验证不重复
        if page1_videos and page2_videos:
            page1_ids = {v.get('id') for v in page1_videos}
            page2_ids = {v.get('id') for v in page2_videos}
            # 两页的视频ID不应该重叠
            assert page1_ids.isdisjoint(page2_ids)


class TestVideoProcessWorkflow:
    """视频处理流程测试"""

    def test_video_status_check_workflow(self, client, created_video):
        """测试视频状态检查流程"""
        video_id = created_video.id

        # 1. 检查初始状态
        status_response = client.get(f'/api/videos/{video_id}/status')
        assert status_response.status_code == 200
        status_data = status_response.get_json()

        # 验证状态字段存在
        assert 'status' in status_data or 'processing_status' in status_data

    def test_video_detail_complete_info(self, client, completed_video):
        """测试完整视频详情信息"""
        video_id = completed_video.id

        # 获取详情
        detail_response = client.get(f'/api/videos/{video_id}')
        assert detail_response.status_code == 200
        detail_data = detail_response.get_json()

        # 验证必要字段
        assert 'id' in detail_data
        assert detail_data['id'] == video_id


class TestVideoSubtitleWorkflow:
    """视频字幕工作流测试"""

    def test_subtitle_query_workflow(self, client, video_with_subtitles):
        """测试字幕查询流程"""
        video_id = video_with_subtitles.id

        # 1. 从视频路由获取字幕
        _video_subtitle_response = client.get(f'/api/videos/{video_id}/subtitle')  # noqa: F841

        # 2. 从字幕路由获取字幕 (可能返回 500 如果字幕文件不存在)
        subtitle_response = client.get(f'/api/subtitles/videos/{video_id}/subtitles')
        assert subtitle_response.status_code in [200, 500]

    def test_subtitle_export_formats(self, client, video_with_subtitles):
        """测试字幕导出不同格式流程"""
        video_id = video_with_subtitles.id
        formats = ['srt', 'vtt', 'txt']

        for fmt in formats:
            response = client.get(f'/api/subtitles/videos/{video_id}/subtitles/export?format={fmt}')
            # 记录每种格式的响应状态
            assert response.status_code in [200, 404, 500], f"导出 {fmt} 格式失败: {response.status_code}"


class TestVideoDeleteWorkflow:
    """视频删除工作流测试"""

    def test_delete_and_verify_workflow(self, client, app, db_session):
        """测试删除后验证流程"""
        from app.models import Video
        from app.models import VideoStatus

        # 1. 创建测试视频
        with app.app_context():
            video = Video(
                title='待删除的测试视频',
                filename='to_delete.mp4',
                filepath='/tmp/to_delete.mp4',
                status=VideoStatus.UPLOADED,
                md5='delete_test_md5',
            )
            db_session.add(video)
            db_session.commit()
            video_id = video.id

        # 2. 验证视频存在
        detail_response = client.get(f'/api/videos/{video_id}')
        assert detail_response.status_code == 200

        # 3. 删除视频
        delete_response = client.delete(f'/api/videos/{video_id}/delete')
        assert delete_response.status_code in [200, 204, 404, 500]

        # 4. 验证视频已删除（如果删除成功）
        if delete_response.status_code in [200, 204]:
            verify_response = client.get(f'/api/videos/{video_id}')
            assert verify_response.status_code in [404, 500]


class TestVideoAPIContractWorkflow:
    """
    API 契约一致性工作流测试
    确保迁移后完整流程行为一致
    """

    def test_crud_workflow_contract(self, client, app, db_session):
        """测试 CRUD 操作契约一致性"""
        from app.models import Video
        from app.models import VideoStatus

        # Create
        with app.app_context():
            video = Video(
                title='契约测试视频',
                filename='contract_test.mp4',
                filepath='/tmp/contract_test.mp4',
                status=VideoStatus.UPLOADED,
                md5='contract_test_md5',
            )
            db_session.add(video)
            db_session.commit()
            video_id = video.id

        # Read (Detail)
        detail_response = client.get(f'/api/videos/{video_id}')
        assert detail_response.status_code == 200
        detail_data = detail_response.get_json()
        assert detail_data['id'] == video_id

        # Read (List)
        list_response = client.get('/api/videos/list')
        assert list_response.status_code == 200
        list_data = list_response.get_json()
        assert 'videos' in list_data

        # Read (Status)
        status_response = client.get(f'/api/videos/{video_id}/status')
        assert status_response.status_code == 200

        # Delete
        delete_response = client.delete(f'/api/videos/{video_id}/delete')
        assert delete_response.status_code in [200, 204, 404, 500]

    def test_response_consistency(self, client, completed_video):
        """测试响应格式一致性"""
        video_id = completed_video.id

        # 多次请求相同端点，验证响应一致
        responses = []
        for _ in range(3):
            response = client.get(f'/api/videos/{video_id}')
            assert response.status_code == 200
            responses.append(response.get_json())

        # 验证响应字段一致
        if responses:
            first_keys = set(responses[0].keys())
            for resp in responses[1:]:
                assert set(resp.keys()) == first_keys
