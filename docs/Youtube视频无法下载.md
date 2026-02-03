# YouTube视频无法下载

## 问题原因
YouTube经常更新其API，导致旧版本的yt-dlp无法正常下载视频。

## 解决方法
升级yt-dlp到最新版本：

```bash
# 激活conda环境
conda activate edumind
# 升级yt-dlp
pip install --upgrade yt-dlp
```
