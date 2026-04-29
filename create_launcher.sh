#!/bin/bash

# 現在のディレクトリを取得
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ICON_PATH="$DIR/icon.png" # アイコン画像があれば

# .desktop ファイルの内容を作成
cat <<EOF > "$HOME/Desktop/DesktopAI.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Desktop AI Mascot
Comment=AI Desktop Assistant
Exec=python3 $DIR/main.py
Path=$DIR
Terminal=false
Categories=Utility;
EOF

# 実行権限を付与
chmod +x "$HOME/Desktop/DesktopAI.desktop"

# GNOMEなどの環境で「起動を許可」する必要がある場合があります
gio set "$HOME/Desktop/DesktopAI.desktop" metadata::trusted true 2>/dev/null || true

echo "Desktop shortcut created on your desktop!"
