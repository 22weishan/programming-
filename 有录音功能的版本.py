# app.py 基础框架
import streamlit as st
import pandas as pd
import librosa
import soundfile as sf
from pydub import AudioSegment
import os

# 页面配置
st.set_page_config(
    page_title="英语听力练习器",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化session state
if 'audio_file' not in st.session_state:
    st.session_state.audio_file = None
if 'playback_rate' not in st.session_state:
    st.session_state.playback_rate = 1.0

# 侧边栏 - 课程选择
with st.sidebar:
    st.title("📚 课程选择")
    lessons = {
        "初级": ["日常对话", "旅行英语", "工作面试"],
        "中级": ["新闻广播", "电影片段", "TED演讲"],
        "高级": ["学术讲座", "商业会议", "纪录片"]
    }
    
    selected_level = st.selectbox("选择难度", list(lessons.keys()))
    selected_lesson = st.selectbox("选择课程", lessons[selected_level])
    
    # 上传音频文件
    uploaded_file = st.file_uploader("或上传音频文件", type=['mp3', 'wav', 'm4a'])
    
    # 字幕文件上传
    subtitle_file = st.file_uploader("上传字幕文件", type=['srt', 'vtt', 'txt', 'pdf'])

# 主界面
st.title("🎧 英语听力练习播放器")

# 播放器控件
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("▶️ 播放", use_container_width=True):
        st.session_state.playing = True
with col2:
    playback_rate = st.slider("播放速度", 0.5, 2.0, 1.0, 0.1)
with col3:
    if st.button("⏸️ 暂停", use_container_width=True):
        st.session_state.playing = False

# 音频可视化
if uploaded_file:
    audio_bytes = uploaded_file.read()
    st.audio(audio_bytes, format='audio/mp3')
    
    # 显示波形图
    st.subheader("📊 音频波形")
    # 这里可以添加音频可视化代码

# 字幕显示区域
st.subheader("📝 字幕")
if subtitle_file:
    subtitles = parse_subtitle(subtitle_file)
    
    # 创建字幕显示区域
    subtitle_container = st.container()
    with subtitle_container:
        for sub in subtitles:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(sub['text'], key=f"sub_{sub['id']}", 
                           use_container_width=True):
                    # 点击跳转到对应时间点
                    st.session_state.seek_time = sub['start']
            with col2:
                if st.button("🔊", key=f"play_{sub['id']}"):
                    # 播放单句
                    play_segment(sub['start'], sub['end'])

# 练习模式
st.subheader("💪 练习模式")
practice_mode = st.selectbox(
    "选择练习模式",
    ["正常模式", "填空模式", "听写模式", "跟读模式"]
)

if practice_mode == "填空模式":
    # 显示带空格的文本
    display_cloze_test()

# 生词本功能
with st.expander("📒 我的生词本"):
    if 'vocabulary' not in st.session_state:
        st.session_state.vocabulary = []
    
    new_word = st.text_input("添加生词")
    if st.button("添加"):
        st.session_state.vocabulary.append(new_word)
    
    for word in st.session_state.vocabulary:
        st.write(f"- {word}")

# 响应式布局
st.markdown("""
<style>
    .stAudio {
        width: 100%;
    }
    .subtitle-button {
        text-align: left;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)
