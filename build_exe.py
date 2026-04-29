import PyInstaller.__main__
import os
import shutil

def build():
    # ビルド設定
    params = [
        'DesktopAI.pyw',           # メインスクリプト
        '--name=DesktopAI',        # 生成されるEXEの名前
        '--onefile',               # 1つのファイルにまとめる
        '--windowed',              # 実行時にコンソールを出さない
        '--clean',                 # ビルド前にキャッシュを削除
        '--noconfirm',             # 上書き確認をスキップ
        # ChromaDBなどの依存関係で必要なデータを含める設定
        '--collect-all=chromadb',
        '--collect-all=posthog',
        '--collect-all=onnxruntime',
    ]

    print("Building EXE... This may take a while.")
    PyInstaller.__main__.run(params)

    # 必要なら、生成後にdistフォルダから取り出すなどの処理
    print("\nBuild completed! Check the 'dist' folder for DesktopAI.exe")

if __name__ == "__main__":
    # PyInstallerがインストールされているか確認
    try:
        import PyInstaller
    except ImportError:
        print("Error: PyInstaller is not installed. Run 'pip install pyinstaller'")
    else:
        build()
