import os
import sys

def get_app_root():
    """
    アプリケーションのルートディレクトリを取得。
    EXE化/AppImage化されている場合は実行ファイルのある場所、
    ソース実行の場合はプロジェクトのルートを返す。
    """
    if hasattr(sys, 'frozen'):
        # PyInstaller (Windows EXE) or AppImage
        # sys.executable は実行ファイル(.exeやAppImage)のパス
        return os.path.dirname(sys.executable)
    
    # ソース実行の場合 (core/path_utils.py から見て2つ上の階層)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_data_path(sub_path):
    """
    指定されたサブパス(plugins, memory_db等)の絶対パスを返す。
    ディレクトリが存在しない場合は作成する。
    """
    root = get_app_root()
    path = os.path.join(root, sub_path)
    
    # 特定のディレクトリは自動作成
    if sub_path in ["plugins", "memory_db", "workspace", "logs"]:
        os.makedirs(path, exist_ok=True)
        # pluginsの場合は__init__.pyも
        if sub_path == "plugins":
            init_py = os.path.join(path, "__init__.py")
            if not os.path.exists(init_py):
                with open(init_py, "w") as f: pass
                
    return path
