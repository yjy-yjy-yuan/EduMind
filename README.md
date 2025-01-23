## AI-EdVision - 智能教育视频分析与个性化辅导系统

### 1. 下载依赖包

### 2. 本项目最好可以是配有GPU的机器，否则可能会出现内存不足的情况：安装CUDA、cuDNN、pytorch等进行加速

### 3. 需要的python版本为： Python > 3.9，最好是python3.10

```shell
pip install -r requirements.txt
```

### 4. 运行程序，实现功能
- 首先切换到IVS目录下，在运行下列命令即可
```shell
streamlit run ../main.py
```

### 5. 需要本地安装并配置完成ffmpeg，参考：https://blog.csdn.net/qq_45956730/article/details/125272407?spm=1001.2014.3001.5506

### 6. 核心组件分析:

- 视频处理模块
main.py作为主控制器
Process_video.py负责核心视频处理功能
video_tools.py提供底层工具支持
download_video.py处理视频下载

- LLM智能交互模块
chat_system.py实现基础对话功能
question_generator.py生成学习问题
learning_path.py生成个性化学习路径

- 笔记系统模块
note_system.py实现带时间戳的笔记功能



