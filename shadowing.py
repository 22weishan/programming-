import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pydub import AudioSegment
from pydub.playback import play
import io
import base64
import tempfile
import os

# 页面配置
st.set_page_config(
    page_title="英语听力练习器",
    page_icon="🎧",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .subtitle-line {
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        cursor: pointer;
        transition: all 0.3s;
    }
    .subtitle-line:hover {
        background-color: #f0f2f6;
    }
    .playing {
        background-color: #e6f7ff !important;
        border-left: 4px solid #1890ff;
    }
    .word-highlight {
        background-color: #fff566;
        padding: 2px 4px;
        border-radius: 3px;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
def init_session_state():
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None
    if 'current_time' not in st.session_state:
        st.session_state.current_time = 0
    if 'is_playing' not in st.session_state:
        st.session_state.is_playing = False
    if 'playback_rate' not in st.session_state:
        st.session_state.playback_rate = 1.0
    if 'vocabulary' not in st.session_state:
        st.session_state.vocabulary = []
    if 'subtitles' not in st.session_state:
        st.session_state.subtitles = []
    if 'current_subtitle' not in st.session_state:
        st.session_state.current_subtitle = 0

init_session_state()

# 解析SRT字幕
def parse_srt(content):
    subtitles = []
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            try:
                # 解析时间戳
                time_line = lines[1]
                start_str, end_str = time_line.split(' --> ')
                
                # 转换时间格式 (HH:MM:SS,mmm -> 秒)
                def time_to_seconds(t):
                    h, m, s = t.split(':')
                    s, ms = s.split(',')
                    return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
                
                start_time = time_to_seconds(start_str)
                end_time = time_to_seconds(end_str)
                
                # 合并文本行
                text = ' '.join(lines[2:])
                
                subtitles.append({
                    'id': lines[0],
                    'start': start_time,
                    'end': end_time,
                    'text': text,
                    'words': text.split()
                })
            except:
                continue
    
    return subtitles

# 侧边栏
with st.sidebar:
    st.title("🎯 学习设置")
    
    # 播放速度控制
    st.session_state.playback_rate = st.slider(
        "播放速度",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1
    )
    
    # 练习模式选择
    practice_mode = st.selectbox(
        "练习模式",
        ["正常模式", "填空练习", "听写练习", "跟读练习"],
        help="选择适合你的练习方式"
    )
    
    # 显示选项
    show_translation = st.checkbox("显示中文翻译", value=True)
    highlight_words = st.checkbox("高亮生词", value=True)
    
    st.divider()
    
    # 课程选择
    st.subheader("📚 课程库")
    lessons = {
        "初级对话": {
            "audio": "samples/beginner_conversation.mp3",
            "subtitle": "samples/beginner_conversation.srt",
            "translation": "这是一段基础对话练习"
        },
        "旅行英语": {
            "audio": "samples/travel_english.mp3", 
            "subtitle": "samples/travel_english.srt",
            "translation": "旅行场景实用英语"
        },
        "商务会议": {
            "audio": "samples/business_meeting.mp3",
            "subtitle": "samples/business_meeting.srt",
            "translation": "商务会议常用表达"
        }
    }
    
    selected_lesson = st.selectbox("选择课程", list(lessons.keys()))
    
    st.divider()
    
    # 上传功能
    st.subheader("📁 上传文件")
    uploaded_audio = st.file_uploader("上传音频", type=['mp3', 'wav', 'm4a'])
    uploaded_subtitle = st.file_uploader("上传字幕", type=['srt', 'txt'])

# 主界面布局
st.title("🎧 英语听力练习播放器")

# 音频播放器
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("▶️ 播放", key="play", type="primary", use_container_width=True):
        st.session_state.is_playing = True
        st.rerun()

with col2:
    # 进度条
    progress = st.slider(
        "播放进度",
        min_value=0,
        max_value=100,
        value=0,
        format="%d%%",
        key="progress_slider"
    )

with col3:
    if st.button("⏸️ 暂停", key="pause", use_container_width=True):
        st.session_state.is_playing = False
        st.rerun()

# 如果用户上传了音频文件
if uploaded_audio:
    # 显示音频播放器
    audio_bytes = uploaded_audio.read()
    st.audio(audio_bytes, format=f"audio/{uploaded_audio.type.split('/')[-1]}")
    
    # 保存到session state
    st.session_state.audio_file = uploaded_audio
    
    # 显示音频信息
    with st.expander("音频信息"):
        st.write(f"文件名: {uploaded_audio.name}")
        st.write(f"文件大小: {len(audio_bytes) / 1024:.1f} KB")

# 如果用户上传了字幕文件
if uploaded_subtitle:
    subtitle_content = uploaded_subtitle.read().decode('utf-8')
    st.session_state.subtitles = parse_srt(subtitle_content)
    
    st.success(f"已加载 {len(st.session_state.subtitles)} 条字幕")

# 显示字幕区域
st.subheader("📝 字幕显示")

if st.session_state.subtitles:
    # 创建字幕显示容器
    subtitle_container = st.container()
    
    with subtitle_container:
        for i, subtitle in enumerate(st.session_state.subtitles):
            # 检查是否是当前播放的字幕
            is_current = (i == st.session_state.current_subtitle)
            css_class = "playing" if is_current else ""
            
            # 创建列布局
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # 显示字幕文本
                if practice_mode == "填空练习":
                    # 填空模式：每句话隐藏部分单词
                    words = subtitle['words']
                    if len(words) > 3:
                        # 随机隐藏一些单词
                        import random
                        display_words = []
                        for word in words:
                            if random.random() < 0.3 and len(word) > 3:
                                display_words.append("___")
                            else:
                                display_words.append(word)
                        display_text = ' '.join(display_words)
                    else:
                        display_text = subtitle['text']
                else:
                    display_text = subtitle['text']
                
                # 创建可点击的字幕行
                if st.button(
                    display_text,
                    key=f"sub_{i}",
                    help=f"点击跳转到 {subtitle['start']:.1f}s",
                    use_container_width=True
                ):
                    st.session_state.current_time = subtitle['start']
                    st.session_state.current_subtitle = i
                    st.rerun()
            
            with col2:
                # 单句重复播放按钮
                if st.button("🔁", key=f"repeat_{i}"):
                    st.info(f"重复播放: {subtitle['text'][:50]}...")
                
                # 添加到生词本
                if st.button("⭐", key=f"star_{i}"):
                    # 让用户选择要添加的单词
                    selected_word = st.selectbox(
                        "选择生词",
                        subtitle['words'],
                        key=f"select_word_{i}"
                    )
                    if selected_word and selected_word not in st.session_state.vocabulary:
                        st.session_state.vocabulary.append(selected_word)
                        st.success(f"已添加: {selected_word}")
    
    # 分页控制（如果字幕很多）
    if len(st.session_state.subtitles) > 20:
        page_size = 20
        total_pages = (len(st.session_state.subtitles) + page_size - 1) // page_size
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            page = st.number_input("页码", min_value=1, max_value=total_pages, value=1)
        
        with col3:
            if st.button("跳转"):
                start_idx = (page - 1) * page_size
                st.session_state.current_subtitle = start_idx
                st.rerun()

else:
    st.info("请上传字幕文件开始练习")

# 练习功能区域
st.subheader("💪 练习工具")

tab1, tab2, tab3 = st.tabs(["生词本", "笔记", "测试"])

with tab1:
    st.write("### 📒 我的生词本")
    
    if st.session_state.vocabulary:
        # 显示生词列表
        for word in st.session_state.vocabulary:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"- **{word}**")
            with col2:
                if st.button("删除", key=f"del_{word}"):
                    st.session_state.vocabulary.remove(word)
                    st.rerun()
        
        # 导出生词本
        if st.button("导出生词本"):
            vocab_text = "\n".join(st.session_state.vocabulary)
            st.download_button(
                label="下载生词本",
                data=vocab_text,
                file_name="my_vocabulary.txt",
                mime="text/plain"
            )
    else:
        st.info("还没有添加生词")

with tab2:
    st.write("### 📝 学习笔记")
    
    # 笔记输入
    note = st.text_area("记录你的学习笔记", height=150)
    
    if st.button("保存笔记"):
        if note:
            # 这里可以保存到数据库或文件
            st.success("笔记已保存！")
            # 显示历史笔记
            if 'notes' not in st.session_state:
                st.session_state.notes = []
            st.session_state.notes.append(note)
    
    # 显示历史笔记
    if 'notes' in st.session_state and st.session_state.notes:
        st.write("### 历史笔记")
        for i, n in enumerate(st.session_state.notes[-5:], 1):
            st.write(f"{i}. {n[:100]}...")

with tab3:
    st.write("### 📝 听力测试")
    
    if st.session_state.subtitles:
        # 从字幕中随机选择句子进行测试
        import random
        
        test_sentence = random.choice(st.session_state.subtitles)['text']
        
        st.write("**听写以下句子：**")
        st.write(f"> {test_sentence}")
        
        user_input = st.text_area("输入你听到的内容", height=100)
        
        if st.button("提交答案"):
            # 简单对比（实际可以更复杂）
            if user_input.strip().lower() == test_sentence.lower():
                st.success("🎉 完全正确！")
            else:
                st.warning("有错误，请再听一遍")
                st.write(f"正确答案：{test_sentence}")

# 响应式音频波形图（简化版）
st.subheader("📊 音频波形")
if st.session_state.audio_file:
    # 创建一个简单的模拟波形图
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines',
        line=dict(color='blue', width=2),
        name='音频波形'
    ))
    
    # 标记当前播放位置
    if 'current_time' in st.session_state:
        fig.add_vline(
            x=st.session_state.current_time % 10,
            line_dash="dash",
            line_color="red"
        )
    
    fig.update_layout(
        height=200,
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("上传音频文件后显示波形图")

# 底部信息
st.divider()
st.caption("🎯 学习建议：每天坚持15分钟，使用不同的练习模式效果更佳！")

# 键盘快捷键提示
with st.expander("🎹 键盘快捷键"):
    st.write("""
    - **空格键**: 播放/暂停
    - **左箭头**: 后退5秒  
    - **右箭头**: 前进5秒
    - **R键**: 重复当前句子
    - **S键**: 保存到生词本
    """)
