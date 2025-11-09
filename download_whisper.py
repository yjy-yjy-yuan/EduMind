import whisper
import os

def download_whisper_model(model_names, download_path="~/Desktop/File/graduation/whisper"):
    """
    下载 Whisper 模型到指定目录，如果目录不存在则自动创建
    
    参数:
        model_names: 模型名称列表
        download_path: 下载路径
    """
    try:
        # 展开用户目录并转换为绝对路径
        download_path = os.path.expanduser(download_path)
        download_path = os.path.abspath(download_path)
        
        # 创建目录（如果不存在）
        if not os.path.exists(download_path):
            os.makedirs(download_path, exist_ok=True)
            print(f"✓ 目录已创建: {download_path}\n")
        else:
            print(f"✓ 目录已存在: {download_path}\n")
        
        # 下载模型
        total = len(model_names)
        for i, model_name in enumerate(model_names, 1):
            try:
                print(f"[{i}/{total}] 正在下载 {model_name} 模型...")
                model = whisper.load_model(model_name, download_root=download_path)
                print(f"✓ {model_name} 模型下载完成！\n")
            except Exception as e:
                print(f"✗ {model_name} 下载失败: {str(e)}\n")
        
        print("=" * 50)
        print("所有模型下载任务完成！")
        
    except PermissionError:
        print(f"✗ 错误：没有权限创建目录 {download_path}")
    except Exception as e:
        print(f"✗ 错误：{str(e)}")

def select_models():
    """让用户选择要下载的模型"""
    available_models = {
        '1': 'tiny',
        '2': 'base',
        '3': 'small',
        '4': 'medium',
        '5': 'large',
        '6': 'turbo',
        '7': 'tiny.en',
        '8': 'base.en',
        '9': 'small.en',
        '10': 'medium.en'
    }
    
    print("=" * 50)
    print("可用的 Whisper 模型:")
    print("=" * 50)
    print("多语言模型:")
    print("  1. tiny     - 最小最快")
    print("  2. base     - 基础版本")
    print("  3. small    - 小型")
    print("  4. medium   - 中型")
    print("  5. large    - 大型（最准确）")
    print("  6. turbo    - 快速版本")
    print("\n仅英语模型:")
    print("  7. tiny.en")
    print("  8. base.en")
    print("  9. small.en")
    print("  10. medium.en")
    print("=" * 50)
    print("\n请输入要下载的模型编号，多个模型用逗号或空格分隔")
    print("例如: 1,3,5 或 1 3 5")
    print("输入 'all' 下载所有模型")
    print("=" * 50)
    
    while True:
        choice = input("\n请选择: ").strip()
        
        if choice.lower() == 'all':
            return list(available_models.values())
        
        # 支持逗号或空格分隔
        choice = choice.replace(',', ' ')
        selections = choice.split()
        
        selected_models = []
        invalid = []
        
        for sel in selections:
            if sel in available_models:
                selected_models.append(available_models[sel])
            else:
                invalid.append(sel)
        
        if invalid:
            print(f"✗ 无效的选择: {', '.join(invalid)}")
            print("请重新输入...")
            continue
        
        if not selected_models:
            print("✗ 未选择任何模型，请重新输入...")
            continue
        
        # 确认选择
        print(f"\n已选择的模型: {', '.join(selected_models)}")
        confirm = input("确认下载? (y/n): ").strip().lower()
        
        if confirm in ['y', 'yes', '是']:
            return selected_models
        else:
            print("已取消，请重新选择...")

# 使用示例
if __name__ == "__main__":
    print("\n欢迎使用 Whisper 模型下载工具")
    
    # 让用户选择模型
    selected = select_models()
    
    # 询问下载路径（可选）
    print("\n" + "=" * 50)
    default_path = "~/Desktop/File/graduation/whisper"
    use_default = input(f"使用默认路径 '{default_path}'? (y/n): ").strip().lower()
    
    if use_default in ['y', 'yes', '是']:
        download_path = default_path
    else:
        download_path = input("请输入下载路径: ").strip()
    
    print("\n" + "=" * 50)
    print("开始下载...")
    print("=" * 50)
    
    # 下载模型
    download_whisper_model(selected, download_path)