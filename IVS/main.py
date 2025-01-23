# main.py
# 主要功能：视频处理、字幕显示、笔记系统、智能问答、学习规划
# 引用了Process_video.py、download_video.py、note_system.py

import streamlit as st
import tempfile
import os
import json
import requests
from Process_video import process_video
from download_video import download_and_play_video
from note_system import NoteSystem, NoteImportance, NoteMood, NoteTemplate
from openai import OpenAI
import logging
from datetime import datetime, timedelta

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

# DeepSeek API配置
API_KEY = "sk-ba656c564e2148009618ad3a2231c002"  # 建议使用环境变量

# DeepSeek对话API类
class DeepSeekChatAPI:
    def __init__(self):
        self.api_key = API_KEY
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        self.messages = []
        
    def chat(self, user_input, stream=True):
        self.messages.append({"role": "user", "content": user_input})
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=self.messages,
                stream=stream
            )
            
            if stream:
                # 流式输出
                full_response = ""
                message_placeholder = st.empty()
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        # 使用markdown方法更新内容
                        message_placeholder.markdown(full_response)
                self.messages.append({"role": "assistant", "content": full_response})
                return full_response
            else:
                # 非流式输出
                result = response.choices[0].message.content
                st.markdown(result)  # 使用markdown而不是write
                self.messages.append({"role": "assistant", "content": result})
                return result
                
        except Exception as e:
            logging.error(f"Chat API Error: {str(e)}")  # 使用logging记录错误
            st.error("抱歉，暂时无法回答您的问题。")
            return "抱歉，暂时无法回答您的问题。"

def submit_chat():
    if st.session_state.chat_input.strip():  # 确保输入不是空白
        st.session_state.submit_chat = True

# 处理本地上传的视频
def process_uploaded_video(uploaded_file, whisper_model_size, video_language):
    """""" 
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        video_path = tmp_file.name
        st.session_state.current_video = video_path
        
    with st.status("Processing video...", expanded=True) as status:
        success = process_video(
            video_path, 
            status, 
            uploaded_file.name, 
            whisper_model=whisper_model_size,
            to_simplified=video_language.startswith("中文")
        )
        if success:
            st.session_state.processed_video = True

# 处理视频链接
def process_video_link(video_link, whisper_model_size, video_language):
    try:
        with st.spinner('正在下载视频...'):
            video_path, video_name = download_and_play_video(video_link)
            
        if video_path and os.path.exists(video_path):
            st.session_state.current_video = video_path
            
            with st.status("Processing video...", expanded=True) as status:
                success = process_video(
                    video_path, 
                    status, 
                    video_name, 
                    whisper_model=whisper_model_size,
                    to_simplified=video_language.startswith("中文")
                )
                if success:
                    st.session_state.processed_video = True
        else:
            st.error("视频下载失败，请检查链接")
            
    except Exception as e:
        st.error(f"处理视频时出错: {str(e)}")

# 处理视频上传和显示
def handle_video_tab():
    video_source = st.radio("选择视频来源", ["本地上传", "视频链接"])
    video_language = st.radio(
        "视频语言",
        options=["中文 (简体/繁体)", "英文 (English)"]
    )
    
    with st.expander("高级设置", expanded=False):
        if video_language.startswith("中文"):
            base_model = st.selectbox(
                "转录模型大小",
                options=["tiny", "base", "small", "medium", "large", "turbo"],
                index=1
            )
        else:
            base_model = st.selectbox(
                "转录模型大小",
                options=["tiny", "base", "small", "medium"],
                index=1
            )
        # 根据语言选择添加.en后缀
        whisper_model_size = f"{base_model}.en" if video_language.startswith("英文") else base_model
        
    if video_source == "本地上传":
        uploaded_file = st.file_uploader("上传视频文件", type=["mp4", "mov", "avi"])
        if uploaded_file and not st.session_state.processed_video:
            process_uploaded_video(uploaded_file, whisper_model_size, video_language)
    else:
        video_link = st.text_input("输入视频链接")
        if st.button("处理视频", key="process_video") and video_link and not st.session_state.processed_video:
            process_video_link(video_link, whisper_model_size, video_language)

    if st.session_state.current_video:
        with st.expander("📺 播放视频", expanded=True):
            st.video(st.session_state.current_video)
            st.markdown(""" 
            <script>
                const video = document.querySelector('video');
                if (video) {
                    video.addEventListener('timeupdate', function() {
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            value: video.currentTime
                        }, '*');
                    });
                }
            </script>
            """, unsafe_allow_html=True)

# 处理字幕显示
def handle_subtitle_tab():
    if st.session_state.video_transcript:
        st.markdown(st.session_state.video_transcript)
    else:
        st.info("请先处理视频以生成字幕")

# 处理智能问答
def handle_qa_tab():
    st.markdown("### 💡 智能问答")
    
    # 初始化聊天历史
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # 用户输入区域（固定高度）
    user_input = st.text_area(
        "在这里输入你的问题",
        height=100,  # 固定高度
        key="qa_input",
        placeholder="请输入你的问题...\n按 Ctrl+Enter 快捷发送",
        help="使用 Ctrl+Enter 快捷发送消息"
    )

    # 创建两列布局用于按钮
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("*提示：使用 Ctrl+Enter 快捷发送*")
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
        </style>
    """, unsafe_allow_html=True)

    # 显示聊天历史
    if st.session_state.messages:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # 检查是否按下了Ctrl+Enter
    if user_input and ('\x11' in user_input or '\x0e' in user_input):  # Ctrl+Enter的一些可能的编码
        user_input = user_input.replace('\x11', '').replace('\x0e', '')  # 清除控制字符
        send_button = True

    # 当点击发送按钮且有输入内容时
    if send_button and user_input and user_input.strip():
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 生成回答
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    deepseek_chat = DeepSeekChatAPI()
                    response = deepseek_chat.chat(user_input)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.markdown(response)
                except Exception as e:
                    st.error(f"生成回答时出错: {str(e)}")
                    st.session_state.messages.pop()  # 移除最后一条用户消息
        
        st.rerun()

    # 添加清空聊天记录按钮（放在底部）
    if st.session_state.messages and st.button("清空聊天记录", key="clear_chat"):
        st.session_state.messages = []
        st.rerun()

def handle_learning_plan():
    st.markdown("### 📚 学习规划")
    
    # 添加视频信息提示
    if not st.session_state.get("current_video"):
        st.warning("请先上传或选择一个视频")
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

def handle_notes():
    if 'note_system' not in st.session_state:
        st.session_state.note_system = NoteSystem()
        
    st.markdown("### 📝 笔记系统")
    
    # 检查是否有视频
    if not st.session_state.get("current_video"):
        st.warning("请先上传或选择一个视频")
        return
    # 检查是否有视频
    if not st.session_state.get("current_video"):
        st.warning("请先上传或选择一个视频")
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