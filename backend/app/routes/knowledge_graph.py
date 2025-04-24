from flask import Blueprint, jsonify, request, current_app
from app.models import Video, Subtitle
from app.models.video import VideoStatus
from app.utils.knowledge_graph_utils import KnowledgeGraphManager
import logging
import threading
import traceback
import json
from services.llm_similarity_service import llm_similarity_service

logger = logging.getLogger(__name__)

# 创建Blueprint
router = Blueprint('knowledge_graph', __name__)

# 配置日志
logger = logging.getLogger(__name__)

# 创建知识图谱管理器实例
kg_manager = KnowledgeGraphManager(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="cjx20040328"
)

# 使用LLM相似度服务
similarity_service = llm_similarity_service

# 存储正在生成的知识图谱任务状态
generation_tasks = {}

# 任务状态常量
TASK_PENDING = 'pending'  # 等待中
TASK_RUNNING = 'running'  # 正在运行
TASK_COMPLETED = 'completed'  # 完成
TASK_FAILED = 'failed'  # 失败

# 视频搜索结果类型
class VideoSearchResult:
    def __init__(self, title, url, source, duration):
        self.title = title
        self.url = url
        self.source = source
        self.duration = duration

# 检查Neo4j连接函数
def check_neo4j_connection():
    """检查Neo4j数据库连接"""
    if not kg_manager.connect():
        logger.error("Neo4j连接失败")
        return False
    kg_manager.close()
    return True

# 获取知识图谱
@router.route('/<video_id>', methods=['GET'])
def get_knowledge_graph(video_id):
    try:
        # 检查是否是合并视频ID（包含下划线）
        is_combined = '_' in str(video_id)
        
        if not is_combined:
            # 如果不是合并视频，检查视频是否存在于数据库中
            try:
                video_id_int = int(video_id)
                video = Video.query.get(video_id_int)
                if not video:
                    return jsonify({'error': '视频不存在'}), 404
            except ValueError:
                return jsonify({'error': '无效的视频ID格式'}), 400
        else:
            # 合并视频ID格式为 "x_y"，不需要在数据库中查询
            logger.info(f"正在获取合并视频 {video_id} 的知识图谱")
        
        # 检查Neo4j连接
        if not check_neo4j_connection():
            return jsonify({'error': '知识图谱数据库连接失败'}), 500
        
        # 获取知识图谱数据
        graph_data = kg_manager.get_knowledge_graph(video_id)
        
        # 如果知识图谱不存在，返回404状态码
        if not graph_data["nodes"]:
            logger.info(f"视频 {video_id} 的知识图谱不存在")
            return jsonify({'error': '该视频的知识图谱不存在'}), 404
        
        return jsonify(graph_data)
            
    except Exception as e:
        logger.error(f"获取知识图谱失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'获取知识图谱失败: {str(e)}'}), 500

# 生成知识图谱
@router.route('/generate/<int:video_id>', methods=['POST'])
def generate_knowledge_graph(video_id):
    try:
        # 检查视频是否存在
        video = Video.query.get(video_id)
        if not video:
            return jsonify({'error': '视频不存在'}), 404
        
        # 检查视频是否已处理完成
        if hasattr(video.status, 'value'):
            # 如果是枚举类型
            if video.status != VideoStatus.COMPLETED:
                return jsonify({'error': f'视频当前状态为 {video.status.value}，必须完成处理才能生成知识图谱'}), 400
        else:
            # 如果是字符串
            if video.status != "completed":
                return jsonify({'error': f'视频当前状态为 {video.status}，必须完成处理才能生成知识图谱'}), 400
        
        # 尝试从数据库获取字幕
        # 直接从文件系统加载字幕数据，不使用数据库字幕记录
        import os
        import json
        from pathlib import Path
        
        # 首先尝试从cache目录查找语义合并的字幕文件
        cache_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads')) / 'cache'
        subtitle_files = []
        
        # 获取视频文件名
        video_name = video.filename.rsplit('.', 1)[0] if video.filename else f'video_{video_id}'
        semantic_file = os.path.join(cache_dir, f'{video_name}_semantic.json')
        
        if os.path.exists(semantic_file):
            current_app.logger.info(f'视频ID {video_id} 在cache目录找到语义合并字幕文件: {semantic_file}')
            subtitle_files.append(semantic_file)
        else:
            # 如果cache目录没有找到，再尝试从subtitles目录查找
            current_app.logger.info(f'视频ID {video_id} 在cache目录未找到语义合并字幕文件，尝试在subtitles目录查找')
            subtitles_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads')) / 'subtitles'
            
            # 查找与视频ID相关的字幕文件
            for file in os.listdir(subtitles_dir):
                if file.endswith('.json') and f'_{video_id}_' in file:
                    subtitle_files.append(os.path.join(subtitles_dir, file))
                    current_app.logger.info(f'视频ID {video_id} 在subtitles目录找到字幕文件: {file}')
                    break
            
        subtitle_text = None  # 初始化字幕文本变量
        
        if subtitle_files:
            try:
                # 从第一个匹配的JSON文件中提取字幕
                with open(subtitle_files[0], 'r', encoding='utf-8') as f:
                    subtitle_data = json.load(f)
                    if isinstance(subtitle_data, list):
                        # 如果是列表格式（语义合并字幕的格式）
                        subtitle_texts = [item.get('text', '') for item in subtitle_data]
                        subtitle_text = ' '.join(subtitle_texts)
                        current_app.logger.info(f'视频ID {video_id} 从文件系统找到字幕数据，共 {len(subtitle_texts)} 条')
                    elif isinstance(subtitle_data, dict) and 'subtitles' in subtitle_data:
                        # 如果是JSON格式的字幕文件
                        subtitle_texts = [item.get('text', '') for item in subtitle_data['subtitles']]
                        subtitle_text = ' '.join(subtitle_texts)
                        current_app.logger.info(f'视频ID {video_id} 从文件系统找到字幕数据，共 {len(subtitle_texts)} 条')
                    else:
                        # 如果是其他格式，尝试直接提取文本
                        subtitle_text = str(subtitle_data)
                        current_app.logger.info(f'视频ID {video_id} 从文件系统找到字幕数据，格式未知')
            except Exception as e:
                current_app.logger.error(f'视频ID {video_id} 从文件系统加载字幕失败: {str(e)}')
                return jsonify({'error': f'加载字幕数据失败: {str(e)}'}), 500
        else:
            # 如果没有找到字幕文件，返回错误
            current_app.logger.error(f'视频ID {video_id} 没有找到字幕文件')
            return jsonify({'error': '没有找到字幕文件，无法生成知识图谱'}), 404
        
        # 检查Neo4j连接
        if not check_neo4j_connection():
            return jsonify({'error': '知识图谱数据库连接失败'}), 500
        
        # 在后台运行知识图谱生成任务
        import threading
        
        # 将任务状态设置为等待中
        generation_tasks[str(video_id)] = TASK_PENDING
        
        # 获取视频标签（如果有）
        video_tags = []
        if video.tags:
            try:
                video_tags = json.loads(video.tags)
                current_app.logger.info(f'视频ID {video_id} 有标签: {video_tags}')
            except json.JSONDecodeError:
                current_app.logger.warning(f'视频ID {video_id} 的标签格式无效: {video.tags}')
        
        thread = threading.Thread(
            target=create_knowledge_graph_task,
            kwargs={
                'video_id': video_id,
                'video_title': video.title or video.filename,
                'subtitle_text': subtitle_text,
                'video_tags': video_tags
            }
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({"message": "知识图谱生成任务已提交，请稍后查看"})
        
    except Exception as e:
        logger.error(f"提交知识图谱生成任务失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'提交知识图谱生成任务失败: {str(e)}'}), 500

# 知识图谱生成任务
def create_knowledge_graph_task(video_id, video_title, subtitle_text, video_tags=None):
    """知识图谱生成任务函数
    
    Args:
        video_id: 视频ID
        video_title: 视频标题
        subtitle_text: 字幕文本
        video_tags: 视频标签列表，默认为空列表
    """
    try:
        # 更新任务状态为运行中
        generation_tasks[str(video_id)] = TASK_RUNNING
        logger.info(f"开始生成视频 {video_id} 的知识图谱...")
        
        # 创建KnowledgeGraphManager实例
        kg_manager = KnowledgeGraphManager()
        
        # 如果没有标签，初始化为空列表
        if video_tags is None:
            video_tags = []
        
        logger.info(f"视频 {video_id} 的标签: {video_tags}")
        
        # 如果有标签，先检查是否有标签相似的视频知识图谱
        combined_with_video = None
        if video_tags and len(video_tags) > 0:
            logger.info(f"检查是否有标签相似的视频知识图谱...")
            
            # 获取所有其他已有知识图谱的视频
            existing_videos = kg_manager.get_all_video_nodes()
            logger.info(f"找到 {len(existing_videos)} 个已有知识图谱的视频")
            
            # 定义相似度阈值
            similarity_threshold = 0.8
            
            # 存储相似视频的列表
            similar_videos = []
            
            # 检查每个已有知识图谱的视频
            for existing_video in existing_videos:
                # 跳过当前视频
                if str(existing_video['video_id']) == str(video_id):
                    continue
                    
                # 获取已有视频的标签
                existing_tags = []
                if existing_video['tags']:
                    try:
                        if isinstance(existing_video['tags'], str):
                            existing_tags = json.loads(existing_video['tags'])
                        else:
                            existing_tags = existing_video['tags']
                    except json.JSONDecodeError:
                        logger.warning(f"视频 {existing_video['video_id']} 的标签格式无效: {existing_video['tags']}")
                
                # 如果已有视频没有标签，跳过
                if not existing_tags:
                    continue
                
                # 计算标签相似度
                similarity = similarity_service.calculate_tag_sets_similarity(video_tags, existing_tags)
                logger.info(f"视频 {video_id} 与视频 {existing_video['video_id']} 的标签相似度: {similarity}")
                
                # 如果相似度超过阈值，添加到相似视频列表
                if similarity >= similarity_threshold:
                    similar_videos.append({
                        'video_id': existing_video['video_id'],
                        'title': existing_video['title'],
                        'similarity': similarity
                    })
            
            # 如果有相似视频，选择相似度最高的进行合并
            if similar_videos:
                # 按相似度降序排序
                similar_videos.sort(key=lambda x: x['similarity'], reverse=True)
                most_similar_video = similar_videos[0]
                
                logger.info(f"找到标签相似的视频: {most_similar_video['video_id']} (相似度: {most_similar_video['similarity']})")
                
                # 先生成当前视频的知识图谱
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(kg_manager.generate_knowledge_graph(video_id, video_title, subtitle_text, video_tags))
                
                if success:
                    # 如果生成成功，尝试合并知识图谱
                    logger.info(f"尝试合并视频 {video_id} 和视频 {most_similar_video['video_id']} 的知识图谱...")
                    
                    # 合并知识图谱
                    combine_success = kg_manager.combine_knowledge_graphs(
                        source_video_id=video_id,
                        target_video_id=most_similar_video['video_id']
                    )
                    
                    if combine_success:
                        logger.info(f"成功合并视频 {video_id} 和视频 {most_similar_video['video_id']} 的知识图谱")
                        combined_with_video = most_similar_video
                    else:
                        logger.error(f"合并视频 {video_id} 和视频 {most_similar_video['video_id']} 的知识图谱失败")
                
                loop.close()
                
                # 更新任务状态为完成
                generation_tasks[str(video_id)] = TASK_COMPLETED
                
                # 返回合并信息
                if combined_with_video:
                    generation_tasks[f"{video_id}_combined_with"] = combined_with_video
                
                return
        
        # 如果没有相似视频或合并失败，正常生成知识图谱
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(kg_manager.generate_knowledge_graph(video_id, video_title, subtitle_text, video_tags))
        loop.close()
        
        if success:
            logger.info(f"视频 {video_id} 的知识图谱生成完成")
            
            # 验证知识图谱数据是否真的存在
            graph_data = kg_manager.get_knowledge_graph(video_id)
            if graph_data and graph_data["nodes"] and len(graph_data["nodes"]) > 0:
                logger.info(f"验证成功: 视频 {video_id} 的知识图谱数据存在，包含 {len(graph_data['nodes'])} 个节点")
                # 更新任务状态为完成
                generation_tasks[str(video_id)] = TASK_COMPLETED
            else:
                logger.error(f"验证失败: 视频 {video_id} 的知识图谱生成标记为成功，但数据不存在")
                # 更新任务状态为失败
                generation_tasks[str(video_id)] = TASK_FAILED
        else:
            logger.error(f"视频 {video_id} 的知识图谱生成失败")
            # 更新任务状态为失败
            generation_tasks[str(video_id)] = TASK_FAILED
    except Exception as e:
        logger.error(f"视频 {video_id} 的知识图谱生成失败: {str(e)}")
        # 更新任务状态为失败
        generation_tasks[str(video_id)] = TASK_FAILED
        logger.error(traceback.format_exc())

# 检查知识图谱生成状态
@router.route('/status/<int:video_id>', methods=['GET'])
def get_knowledge_graph_status(video_id):
    try:
        # 打印当前所有任务状态，用于调试
        logger.info(f"当前任务状态列表: {generation_tasks}")
        
        # 检查视频是否存在
        video = Video.query.get(video_id)
        if not video:
            logger.warning(f"视频 {video_id} 不存在")
            return jsonify({'error': '视频不存在'}), 404
        
        # 获取任务状态
        task_status = generation_tasks.get(str(video_id))
        logger.info(f"视频 {video_id} 的任务状态: {task_status}")
        
        # 如果任务状态不存在，尝试检查知识图谱是否存在
        if task_status is None:
            # 尝试获取知识图谱数据
            graph_data = kg_manager.get_knowledge_graph(video_id)
            
            # 如果知识图谱存在，设置状态为已完成
            if graph_data["nodes"]:
                logger.info(f"视频 {video_id} 的知识图谱已存在，设置状态为已完成")
                generation_tasks[str(video_id)] = TASK_COMPLETED
                return jsonify({'status': TASK_COMPLETED})
            else:
                logger.warning(f"视频 {video_id} 的知识图谱不存在且没有生成任务")
                return jsonify({'error': '视频的知识图谱生成任务不存在'}), 404
        
        return jsonify({'status': task_status})
        
    except Exception as e:
        logger.error(f"获取知识图谱生成状态失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'获取知识图谱生成状态失败: {str(e)}'}), 500

# 搜索相关视频
@router.route('/search-videos', methods=['POST'])
def search_videos():
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据格式错误'}), 400
            
        keyword = data.get('keyword')
        video_type = data.get('type')
        expanded = data.get('expanded', [])
        
        if not keyword:
            return jsonify({'error': '关键词不能为空'}), 400
            
        # 使用知识图谱管理器搜索相关视频
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        videos = loop.run_until_complete(kg_manager.search_related_videos(
            keyword=keyword,
            video_type=video_type,
            expanded=expanded
        ))
        loop.close()
        
        return jsonify({"videos": videos})
        
    except Exception as e:
        logger.error(f"搜索视频失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'搜索视频失败: {str(e)}'}), 500


