import PyInstaller.__main__
import os
import sys

def build():
    # 実行ファイル名の設定
    exe_name = 'DesktopAI'
    if sys.platform == 'win32':
        exe_name += '.exe'

    params = [
        'DesktopAI.pyw',           # メインスクリプト
        f'--name={exe_name}',      # 生成されるEXE/実行ファイルの名前
        '--onefile',               # 1つのファイルにまとめる
        '--windowed',              # 実行時にコンソールを出さない
        '--clean',                 # ビルド前にキャッシュを削除
        '--noconfirm',             # 上書き確認をスキップ
        # ChromaDBとその依存関係のメタデータを確実にコピー
        '--copy-metadata=chromadb',
        '--copy-metadata=tqdm',
        '--copy-metadata=regex',
        '--copy-metadata=requests',
        '--copy-metadata=packaging',
        '--copy-metadata=filelock',
        '--copy-metadata=numpy',
        '--copy-metadata=tokenizers',
        '--copy-metadata=onnxruntime',
        # ファイル一式も収集
        '--collect-all=chromadb',
        '--collect-all=onnxruntime',
        '--collect-all=PyQt5',
        '--hidden-import=PyQt5.sip',
    ]

    print("Building executable... This may take a while.")
    try:
        PyInstaller.__main__.run(params)
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)

    print("\nBuild completed!")

if __name__ == "__main__":
    build()
