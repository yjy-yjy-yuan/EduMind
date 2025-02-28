# 功能：测试依赖

from flask import Flask, __version__ as flask_version
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import requests
from pytube import YouTube
import cv2
from bilibili_api import video, sync

def test_imports():
    print("Flask version:", flask_version)
    print("OpenCV version:", cv2.__version__)
    print("All dependencies imported successfully!")

if __name__ == "__main__":
    test_imports()
