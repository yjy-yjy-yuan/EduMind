import warnings
import torchvision
torchvision.disable_beta_transforms_warning()
warnings.filterwarnings('ignore', category=UserWarning)

# main.py
# 主要功能：视频处理、字幕显示、笔记系统、智能问答、学习规划
# 引用了Process_video.py、download_video.py、note_system.py

import streamlit as st
import tempfile
import os
import json
import requests
from openai import OpenAI
from Process_video import process_video
from download_video import download_and_play_video
from note_system import NoteSystem, NoteImportance, NoteMood, NoteTemplate
from rag_system import RAGSystem
import logging
from datetime import datetime, timedelta
import hashlib
import time
import random

# 设置页面配置
st.set_page_config(
    page_title="智能教育视频分析系统",
    page_icon="🎓",
    layout="wide"
)

# 配置日志
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, f"streamlit_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 通义千问 API配置
API_KEY = "sk-178e130a121445659860893fdfae1e7d"  # 建议使用环境变量

# 通义千问对话API类
class QwenChatAPI:
    def __init__(self):
        self.client = OpenAI(
            api_key=API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        # 分别存储两种模式的消息历史
        self.video_qa_messages = [
            {"role": "system", "content": "你是一个教育助手。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。"}
        ]
        self.free_chat_messages = [
            {"role": "system", "content": "你是一个教育助手。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。"}
        ]
        # 添加请求计数器和最后请求时间
        self.request_count = 0
        self.last_request_time = 0
        self.max_retries = 3
        self.retry_delay = 1.5

    def _wait_for_rate_limit(self):
        """等待以符合速率限制"""
        current_time = time.time()
        time_diff = current_time - self.last_request_time
        
        # 如果距离上次请求不到1秒
        if time_diff < 1:
            # 添加一个随机延迟，避免所有请求同时发送
            sleep_time = 1 - time_diff + random.uniform(0, 0.5)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    def _make_request(self, messages, retry_count=0):
        """发送API请求，包含重试逻辑"""
        try:
            self._wait_for_rate_limit()
            
            stream_response = self.client.chat.completions.create(
                model="qwen-turbo",
                messages=messages,
                temperature=0.3,
                stream=True
            )
            return stream_response
            
        except Exception as e:
            if "rate_limit_reached_error" in str(e) and retry_count < self.max_retries:
                # 如果是速率限制错误且未超过最大重试次数
                retry_sleep = self.retry_delay * (retry_count + 1)
                time.sleep(retry_sleep)
                return self._make_request(messages, retry_count + 1)
            else:
                raise e

    def _judge_question_type(self, question: str) -> bool:
        """判断是否需要分析整个视频内容"""
        judge_prompt = f"""请判断以下问题是否需要分析整个视频内容来回答：

问题：{question}

判断标准：
1. 如果问题涉及视频的整体内容、主题、总结等（如"视频讲了什么"、"视频的主要内容是什么"、"总结一下视频内容"等），返回"需要全文分析"
2. 如果问题是具体的、针对特定内容的提问，返回"使用RAG检索"

请只返回"需要全文分析"或"使用RAG检索"这两个短语之一。"""

        try:
            messages = [{"role": "user", "content": judge_prompt}]
            self._wait_for_rate_limit()  # 添加速率限制等待
            response = self.client.chat.completions.create(
                model="qwen-turbo",
                messages=messages,
                temperature=0.3,
            )
            result = response.choices[0].message.content.strip()
            return result == "需要全文分析"
        except Exception as e:
            logging.error(f"Question type judgment error: {str(e)}")
            return False

    def chat(self, user_input, mode="free_chat", context=None, full_transcript=None, stream=True):
        """流式对话函数"""
        # 选择对应模式的消息历史
        messages = self.video_qa_messages if mode == "video_qa" else self.free_chat_messages
        
        try:
            if mode == "video_qa":
                # 判断是否需要分析整个视频内容
                needs_full_analysis = self._judge_question_type(user_input)
                
                if needs_full_analysis and full_transcript:
                    # 使用完整字幕进行回答
                    prompt = f"""请基于以下完整的视频字幕回答用户的问题。

用户问题：{user_input}

完整视频字幕：
{full_transcript}

请给出全面、详细的回答。回答要求：
1. 分条列点说明
2. 使用markdown格式
3. 突出重点内容"""
                else:
                    # 使用相关字幕片段进行回答
                    prompt = f"""请基于以下视频片段回答用户的问题。

用户问题：{user_input}

{context}

请给出准确、相关的回答。回答要求：
1. 分条列点说明
2. 使用markdown格式
3. 突出重点内容
4. 如果提供的视频片段无法完全回答问题，请说明"""
            else:
                # 自由对话模式
                prompt = user_input

            # 添加用户消息
            messages.append({"role": "user", "content": prompt})
            
            # 创建流式对话（使用重试机制）
            stream_response = self._make_request(messages)
            
            # 用于收集完整的回答
            full_response = ""
            
            # 逐个词语返回回答
            for chunk in stream_response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # 添加助手回答到历史记录
            messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            error_msg = f"对话生成出错: {str(e)}"
            logging.error(f"Chat API Error: {str(e)}")
            yield error_msg

def submit_chat():
    if st.session_state.chat_input.strip():  # 确保输入不是空白
        st.session_state.submit_chat = True

# 处理本地上传的视频
def process_uploaded_video(uploaded_file, whisper_model_size, video_language):
    """处理上传的视频文件"""
    if uploaded_file is not None:
        try:
            # 保存视频数据到session state
            video_data = uploaded_file.getvalue()
            st.session_state.video_data = video_data
            
            # 创建临时文件用于处理
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                tmp_file.write(video_data)
                video_path = tmp_file.name

            # 处理视频
            with st.spinner('处理视频中...'):
                process_video(
                    video_path,
                    original_filename=uploaded_file.name,
                    whisper_model=whisper_model_size,
                    st_session_state=st.session_state
                )
                
            st.session_state.processed_video = True
            return True

        except Exception as e:
            st.error(f'处理视频时出错: {str(e)}')
            return False
        finally:
            # 清理临时文件
            if 'video_path' in locals():
                try:
                    os.unlink(video_path)
                except:
                    pass
    return False

def process_video_link(video_link, whisper_model_size, video_language):
    """处理视频链接"""
    if video_link:
        try:
            # 下载视频
            with st.spinner('下载视频中...'):
                video_path_info = download_and_play_video(video_link)
                if not video_path_info[0]:  # 检查 video_path
                    st.error('下载视频失败')
                    return False
                
                video_path = video_path_info[0]  # 获取实际的视频路径
                st.success(f"视频已下载到: {video_path}")
                
                # 读取视频数据
                with open(video_path, 'rb') as f:
                    video_data = f.read()
                st.session_state.video_data = video_data

            # 处理视频
            with st.spinner('处理视频中...'):
                process_video(
                    video_path,
                    whisper_model=whisper_model_size,
                    st_session_state=st.session_state
                )
                
            st.session_state.processed_video = True
            return True

        except Exception as e:
            st.error(f'处理视频时出错: {str(e)}')
            return False
        finally:
            # 清理临时文件
            if 'video_path' in locals() and os.path.exists(video_path):
                try:
                    os.unlink(video_path)
                except:
                    pass
    return False

def handle_video_tab():
    """处理视频上传和显示标签页"""
    st.header("📹 视频处理")
    
    # 初始化session state
    if 'processed_video' not in st.session_state:
        st.session_state.processed_video = False
    if 'video_data' not in st.session_state:
        st.session_state.video_data = None
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "upload"  # 默认显示上传标签页
        
    # 选择whisper模型大小
    whisper_model_size = st.selectbox(
        "选择Whisper模型大小",
        ["tiny", "base", "small", "medium", "large"],
        index=1
    )
    
    # 选择视频语言
    video_language = st.selectbox(
        "选择视频语言",
        ["Chinese", "English", "Japanese", "Korean"],
        index=0
    )

    # 创建选项卡
    tab1, tab2 = st.tabs(["📤 本地视频上传", "🔗 视频链接输入"])
    
    # 本地视频上传标签页
    with tab1:
        if not st.session_state.processed_video:
            uploaded_file = st.file_uploader("选择视频文件", type=["mp4", "mov", "avi"])
            if uploaded_file:
                if st.button("处理本地视频"):
                    process_uploaded_video(uploaded_file, whisper_model_size, video_language)
        else:
            st.info("已有视频正在处理中。如需处理新视频，请刷新页面。")
    
    # 视频链接输入标签页
    with tab2:
        if not st.session_state.processed_video:
            video_link = st.text_input("输入视频链接（支持B站、YouTube等平台）", key="video_link_input")
            # 始终显示按钮，但根据是否有输入来决定是否禁用
            if st.button("处理在线视频", disabled=not bool(video_link), key="process_video_button"):
                process_video_link(video_link, whisper_model_size, video_language)
        else:
            st.info("已有视频正在处理中。如需处理新视频，请刷新页面。")

    # 显示视频和处理状态
    if st.session_state.processed_video:
        st.success("✅ 视频已成功处理")
        
    if st.session_state.video_data is not None:
        with st.expander("📺 播放视频", expanded=True):
            st.video(st.session_state.video_data)
            
    # 添加重置按钮
    if st.session_state.processed_video:
        if st.button("处理新视频"):
            st.session_state.processed_video = False
            st.session_state.video_data = None
            st.experimental_rerun()

# 处理字幕显示
def handle_subtitle_tab():
    if st.session_state.video_transcript:
        st.markdown(st.session_state.video_transcript)
    else:
        st.info("请先处理视频以生成字幕")

# 处理智能问答
def handle_qa_tab():
    st.markdown("### 💡 智能问答")
    
    # 初始化两种模式的聊天历史
    if 'video_qa_messages' not in st.session_state:
        st.session_state.video_qa_messages = []
    if 'free_chat_messages' not in st.session_state:
        st.session_state.free_chat_messages = []
    
    # 初始化通义千问 API
    if 'qwen_api' not in st.session_state:
        st.session_state.qwen_api = QwenChatAPI()
    
    # 初始化输入框的key
    if 'qa_input_key' not in st.session_state:
        st.session_state.qa_input_key = 0

    # 添加选择器，让用户选择是否基于视频内容进行问答
    use_video_content = st.radio(
        "选择问答模式",
        ["基于视频内容的智能问答", "自由对话模式"],
        index=0,  # 默认选择基于视频内容
        help="基于视频内容：分析视频内容回答问题\n自由对话：可以询问任何问题"
    )

    # 根据当前模式选择对应的消息列表
    current_messages = (st.session_state.video_qa_messages 
                       if use_video_content == "基于视频内容的智能问答" 
                       else st.session_state.free_chat_messages)

    # 添加清除聊天记录按钮
    col1, col2, col3 = st.columns([6, 2, 2])
    with col2:
        if st.button("清除聊天记录", use_container_width=True):
            if use_video_content == "基于视频内容的智能问答":
                st.session_state.video_qa_messages = []
            else:
                st.session_state.free_chat_messages = []
            st.rerun()

    if use_video_content == "基于视频内容的智能问答":
        # 检查是否有视频数据和转录文本
        if not st.session_state.get("video_data") or not st.session_state.get("video_transcript"):
            st.warning("请先上传并处理视频")
            return
    
    # 用户输入区域（固定高度）
    user_input = st.text_area(
        "在这里输入你的问题",
        key=f"qa_input_{st.session_state.qa_input_key}",
        height=100,
        placeholder="请输入你的问题...",
    )

    # 创建两列布局用于按钮
    col1, col2 = st.columns([4, 1])
    with col1:
        if use_video_content == "基于视频内容的智能问答":
            st.markdown("*提示：系统将基于视频内容为您解答问题*")
        else:
            st.markdown("*提示：您可以询问任何问题*")
    with col2:
        send_button = st.button("发送", use_container_width=True)

    # 设置消息显示容器的样式
    st.markdown("""
        <style>
        .stChatMessage {
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        .stChatMessage:hover {
            background-color: #f0f0f0;
        }
        .timestamp-link {
            color: #0066cc;
            text-decoration: underline;
            cursor: pointer;
        }
        </style>
    """, unsafe_allow_html=True)

    # 显示当前模式的聊天历史
    if current_messages:
        # 创建一个容器来显示聊天记录
        chat_container = st.container()
        with chat_container:
            for message in current_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"], unsafe_allow_html=True)

    # 当点击发送按钮且有输入内容时
    if send_button and user_input and user_input.strip():
        current_input = user_input.strip()
        
        # 添加用户消息到当前模式的消息列表
        current_messages.append({"role": "user", "content": current_input})
        with st.chat_message("user"):
            st.markdown(current_input)

        # 根据用户选择决定使用哪种问答模式
        if use_video_content == "基于视频内容的智能问答":
            # 使用RAG系统搜索相关字幕
            similar_subtitles = st.session_state.rag_system.search_similar_subtitles(current_input)
            
            # 构建上下文
            context = "相关视频内容：\n"
            for sub in similar_subtitles:
                context += f"- [{sub['start_time']} --> {sub['end_time']}] {sub['text']} (相关度: {sub['similarity_score']:.2f})\n"
            
            # 获取AI回答（视频问答模式）
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # 使用流式输出
                for token in st.session_state.qwen_api.chat(
                    user_input=current_input,
                    mode="video_qa",
                    context=context,
                    full_transcript=st.session_state.video_transcript
                ):
                    full_response += token
                    message_placeholder.markdown(full_response + "▌")
                
                # 显示最终回答
                message_placeholder.markdown(full_response)
                current_messages.append({"role": "assistant", "content": full_response})
        else:
            # 自由对话模式：直接使用通义千问对话
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # 使用流式输出
                for token in st.session_state.qwen_api.chat(
                    user_input=current_input,
                    mode="free_chat"
                ):
                    full_response += token
                    message_placeholder.markdown(full_response + "▌")
                
                # 显示最终回答
                message_placeholder.markdown(full_response)
                current_messages.append({"role": "assistant", "content": full_response})

        # 通过更新key来清空输入框
        st.session_state.qa_input_key += 1
        st.rerun()
    
    # 学习规划功能实现
def handle_learning_plan():
    st.markdown("### 📚 学习规划")
    
    # 检查是否有视频数据和转录文本
    if not st.session_state.get("video_data") or not st.session_state.get("video_transcript"):
        st.warning("请先上传并处理视频")
        return
    
    # 初始化学习计划
    if "learning_plan" not in st.session_state:
        st.session_state.learning_plan = ""
        
    # 生成学习计划按钮
    if st.button("生成学习计划", use_container_width=True):
        with st.spinner("正在生成学习计划..."):
            try:
                deepseek_chat = DeepSeekChatAPI()
                # 构建提示词
                prompt = f"""请根据以下视频内容生成一个详细的学习计划：
                视频标题：{st.session_state.current_video}
                
                请包含以下内容：
                1. 学习目标
                2. 关键知识点
                3. 学习步骤
                4. 练习建议
                5. 时间安排
                
                请用markdown格式输出。
                """
                response = deepseek_chat.chat(prompt)
                st.session_state.learning_plan = response
                st.rerun()
            except Exception as e:
                st.error(f"生成学习计划时出错: {str(e)}")
    
    # 显示学习计划
    if st.session_state.learning_plan:
        st.markdown(st.session_state.learning_plan)

# 笔记系统功能实现
def handle_notes():
    if 'note_system' not in st.session_state:
        st.session_state.note_system = NoteSystem()
        
    st.markdown("### 📝 笔记系统")
    
    # 检查是否有视频数据和转录文本
    if not st.session_state.get("video_data") or not st.session_state.get("video_transcript"):
        st.warning("请先上传并处理视频")
        return
        
    # 添加笔记部分
    with st.expander("✍️ 添加新笔记", expanded=True):
        # 笔记模板选择
        template_type = st.selectbox(
            "选择笔记模板",
            options=[None] + list(NoteTemplate),
            format_func=lambda x: "不使用模板" if x is None else x.value
        )
        
        # 如果选择了模板，显示模板内容
        if template_type:
            note_template = st.session_state.note_system.get_template(template_type)
            note_text = st.text_area("笔记内容", value=note_template, height=200)
        else:
            note_text = st.text_area("笔记内容", height=150)
        
        col1, col2 = st.columns(2)
        with col1:
            importance = st.select_slider(
                "重要性",
                options=list(NoteImportance),
                format_func=lambda x: f"{x.value} {x.name}",
                value=NoteImportance.LOW
            )
        with col2:
            mood = st.select_slider(
                "理解程度",
                options=list(NoteMood),
                format_func=lambda x: f"{x.value} {x.name}",
                value=NoteMood.NEUTRAL
            )
        
        tags = st.text_input("标签（用逗号分隔）")
        tags_set = {tag.strip() for tag in tags.split(",")} if tags else set()
        
        current_time = st.session_state.get('current_video_time', 0)
        if st.button("保存笔记"):
            if note_text.strip():
                success = st.session_state.note_system.add_note(
                    text=note_text,
                    timestamp=current_time,
                    importance=importance,
                    mood=mood,
                    tags=tags_set,
                    template_type=template_type
                )
                if success:
                    st.success("笔记已保存！")
                else:
                    st.error("保存笔记失败！")
                    
    # 显示笔记列表
    with st.expander("📖 查看笔记", expanded=True):
        # 筛选选项
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_importance = st.selectbox(
                "按重要性筛选",
                options=[None] + list(NoteImportance),
                format_func=lambda x: "全部" if x is None else f"{x.value} {x.name}"
            )
        with col2:
            filter_mood = st.selectbox(
                "按理解程度筛选",
                options=[None] + list(NoteMood),
                format_func=lambda x: "全部" if x is None else f"{x.value} {x.name}"
            )
        with col3:
            all_tags = {tag for note in st.session_state.note_system.notes for tag in note.tags}
            filter_tags = st.multiselect("按标签筛选", options=list(all_tags))
            
        notes = st.session_state.note_system.get_notes(
            importance=filter_importance,
            mood=filter_mood,
            tags=set(filter_tags) if filter_tags else None
        )
        
        if not notes:
            st.info("还没有添加任何笔记")
        else:
            for note in notes:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**时间**: [{note.timestamp_str}] {note.importance.value} {note.mood.value}")
                        if note.tags:
                            st.markdown(f"**标签**: {', '.join(note.tags)}")
                        st.markdown(f"**内容**:\n{note.text}")
                    with col2:
                        if st.button("删除", key=f"delete_{note.id}"):
                            st.session_state.note_system.delete_note(note.id)
                            st.rerun()
                        if st.button("标记已复习", key=f"review_{note.id}"):
                            st.session_state.note_system.mark_note_reviewed(note.id)
                            st.success("已标记为已复习！")
                    st.markdown("---")
            
            # 添加笔记总结功能
            if st.button("生成笔记总结", key="summarize_notes"):
                with st.spinner("正在生成笔记总结..."):
                    deepseek_chat = DeepSeekChatAPI()
                    notes_text = "\n".join([
                        f"时间 {note.timestamp_str} {note.importance.value}: {note.text}" 
                        for note in notes
                    ])
                    
                    summary = deepseek_chat.chat(f"请总结这些笔记内容：\n{notes_text}")
                    st.markdown("### 笔记总结")
                    st.markdown(summary)
            
            # 显示学习进度
            if st.button("查看学习进度"):
                progress = st.session_state.note_system.get_learning_progress()
                st.markdown("### 📊 学习进度统计")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("总笔记数", progress["total_notes"])
                    st.metric("已复习比例", f"{progress['review_status']['reviewed']*100:.1f}%")
                
                with col2:
                    st.markdown("#### 重要性分布")
                    for imp, ratio in progress["importance_distribution"].items():
                        st.progress(ratio, text=f"{NoteImportance[imp].value} {ratio*100:.1f}%")
                    
                    st.markdown("#### 理解程度分布")
                    for mood, ratio in progress["mood_distribution"].items():
                        st.progress(ratio, text=f"{NoteMood[mood].value} {ratio*100:.1f}%")
                
                if progress["tags_distribution"]:
                    st.markdown("#### 标签统计")
                    for tag, ratio in progress["tags_distribution"].items():
                        st.progress(ratio, text=f"{tag}: {ratio*100:.1f}%")

# 主函数
def main():
    st.title("智能教育视频分析系统")
    
    # 初始化会话状态变量
    if 'current_video' not in st.session_state:
        st.session_state.current_video = None
    if 'video_transcript' not in st.session_state:
        st.session_state.video_transcript = None
    if 'note_system' not in st.session_state:
        st.session_state.note_system = NoteSystem()
    if 'current_video_time' not in st.session_state:
        st.session_state.current_video_time = 0
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "视频处理"
    if 'processed_video' not in st.session_state:
        st.session_state.processed_video = False
    if 'learning_plan' not in st.session_state:
        st.session_state.learning_plan = None
    if 'chat_input' not in st.session_state:
        st.session_state.chat_input = ""
    if 'submit_chat' not in st.session_state:
        st.session_state.submit_chat = False
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = RAGSystem()
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # 创建三列布局
    col1, col2, col3 = st.columns([2, 3, 2])
    
    # 左侧列：视频上传和显示
    with col1:
        handle_video_tab()
    
    # 中间列：功能区
    with col2:
        tab1, tab2, tab3 = st.tabs(["📝 字幕", "💡 智能问答", "📚 学习规划"])
        with tab1:
            handle_subtitle_tab()
        with tab2:
            handle_qa_tab()
        with tab3:
            handle_learning_plan()
    
    # 右侧列：笔记系统
    with col3:
        handle_notes()

# 启动应用
if __name__ == "__main__":
    main()