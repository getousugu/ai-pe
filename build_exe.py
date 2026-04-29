import PyInstaller.__main__
import os
import sys

def build():
    # ビルド設定
    params = [
        'DesktopAI.pyw',           # メインスクリプト
        '--name=DesktopAI',        # 生成されるEXEの名前
        '--onefile',               # 1つのファイルにまとめる
        '--windowed',              # 実行時にコンソールを出さない
        '--clean',                 # ビルド前にキャッシュを削除
        '--noconfirm',             # 上書き確認をスキップ
        '--hidden-import=pkg_resources.py2_warn', # よくあるエラー対策
        '--collect-submodules=chromadb',
        '--copy-metadata=chromadb',
        '--copy-metadata=tqdm',
        '--copy-metadata=regex',
        '--copy-metadata=requests',
        '--copy-metadata=packaging',
        '--copy-metadata=filelock',
        '--copy-metadata=numpy',
        '--copy-metadata=tokenizers',
        '--copy-metadata=onnxruntime',
    ]

    print("Building EXE... This may take a while.")
    try:
        PyInstaller.__main__.run(params)
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)

    print("\nBuild completed! Check the 'dist' folder for DesktopAI.exe")

if __name__ == "__main__":
    build()
