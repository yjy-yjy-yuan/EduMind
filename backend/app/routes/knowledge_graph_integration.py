"""
知识图谱整合相关路由
"""
import os
import json
import logging
import traceback
from flask import Blueprint, request, jsonify, current_app
from ..models.video import Video
from ..extensions import db
from ..utils.knowledge_graph_utils import KnowledgeGraphManager
from services.llm_similarity_service import llm_similarity_service

# 创建蓝图
integration_bp = Blueprint('knowledge_graph_integration', __name__)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@integration_bp.route('/find-similar/<int:video_id>', methods=['GET'])
def find_similar_videos(video_id):
    """
    查找与指定视频标签相似的其他视频
    
    Args:
        video_id: 目标视频ID
        
    Returns:
        相似视频列表
    """
    try:
        # 获取目标视频
        target_video = Video.query.get(video_id)
        if not target_video:
            return jsonify({'error': '视频不存在'}), 404
            
        # 获取目标视频标签
        target_tags = []
        if target_video.tags:
            try:
                target_tags = json.loads(target_video.tags)
            except json.JSONDecodeError:
                logger.warning(f"视频 {video_id} 的标签格式无效: {target_video.tags}")
        
        if not target_tags:
            return jsonify({'error': '目标视频没有标签'}), 400
            
        # 获取所有其他视频
        all_videos = Video.query.filter(Video.id != video_id).all()
        all_video_data = []
        
        for video in all_videos:
            video_data = {
                'id': video.id,
                'title': video.title or video.filename,
                'tags': video.tags
            }
            all_video_data.append(video_data)
            
        # 查找相似视频
        similar_threshold = float(request.args.get('threshold', 0.6))
        similar_limit = int(request.args.get('limit', 5))
        
        similar_videos = llm_similarity_service.find_similar_videos(
            target_tags, 
            all_video_data, 
            threshold=similar_threshold,
            limit=similar_limit
        )
        
        # 格式化返回结果
        result = []
        for item in similar_videos:
            video = item['video']
            result.append({
                'id': video['id'],
                'title': video['title'],
                'similarity': item['similarity'],
                'tags': json.loads(video['tags']) if isinstance(video['tags'], str) else video['tags']
            })
            
        return jsonify({
            'target_video': {
                'id': target_video.id,
                'title': target_video.title or target_video.filename,
                'tags': target_tags
            },
            'similar_videos': result
        })
        
    except Exception as e:
        logger.error(f"查找相似视频时发生错误: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'查找相似视频失败: {str(e)}'}), 500

@integration_bp.route('/combine', methods=['POST'])
def combine_knowledge_graphs():
    """
    整合两个视频的知识图谱
    
    请求体格式:
    {
        "source_video_id": 1,
        "target_video_id": 2
    }
    
    Returns:
        整合结果
    """
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
            
        source_video_id = data.get('source_video_id')
        target_video_id = data.get('target_video_id')
        
        if not source_video_id or not target_video_id:
            return jsonify({'error': '源视频ID和目标视频ID不能为空'}), 400
            
        # 获取视频信息
        source_video = Video.query.get(source_video_id)
        target_video = Video.query.get(target_video_id)
        
        if not source_video:
            return jsonify({'error': f'源视频(ID={source_video_id})不存在'}), 404
            
        if not target_video:
            return jsonify({'error': f'目标视频(ID={target_video_id})不存在'}), 404
            
        # 获取视频标签
        source_tags = []
        target_tags = []
        
        if source_video.tags:
            try:
                source_tags = json.loads(source_video.tags)
            except json.JSONDecodeError:
                logger.warning(f"源视频 {source_video_id} 的标签格式无效: {source_video.tags}")
                
        if target_video.tags:
            try:
                target_tags = json.loads(target_video.tags)
            except json.JSONDecodeError:
                logger.warning(f"目标视频 {target_video_id} 的标签格式无效: {target_video.tags}")
        
        # 检查标签相似度
        force_combine = data.get('force_combine', False)
        threshold = float(data.get('threshold', 0.7))
        
        if not force_combine:
            can_combine = llm_similarity_service.can_combine_knowledge_graphs(
                source_tags, target_tags, threshold=threshold
            )
            
            if not can_combine:
                return jsonify({
                    'error': '视频标签相似度不足，无法自动整合知识图谱',
                    'source_tags': source_tags,
                    'target_tags': target_tags,
                    'can_force': True
                }), 400
        
        # 创建知识图谱管理器
        kg_manager = KnowledgeGraphManager()
        
        # 整合知识图谱
        success = kg_manager.combine_knowledge_graphs(source_video_id, target_video_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'成功整合视频 {source_video_id} 和视频 {target_video_id} 的知识图谱'
            })
        else:
            return jsonify({
                'error': '知识图谱整合失败',
                'can_force': True
            }), 500
            
    except Exception as e:
        logger.error(f"整合知识图谱时发生错误: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'整合知识图谱失败: {str(e)}'}), 500
