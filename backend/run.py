"""Flask应用入口，用于启动应用"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
