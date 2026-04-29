import os
import sys
import json
import subprocess
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QLineEdit, QApplication, QMenu, QTextBrowser, QAction
from PyQt5.QtCore import Qt, QPoint, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor

from ui.settings_dialog import SettingsDialog
from core.api_manager import APIManager
from core.llm_client import LLMClient
from core.reminder_manager import ReminderManager
from core.skill_manager import SkillManager
from core.path_utils import get_app_root, get_data_path

class ChatThread(QThread):
    response_ready = pyqtSignal(str)
    
    def __init__(self, llm_client, text, image_path=None):
        super().__init__()
        self.llm_client = llm_client
        self.text = text
        self.image_path = image_path
        
    def run(self):
        resp = self.llm_client.generate_response(self.text, self.image_path)
        self.response_ready.emit(resp)

class DesktopPetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.api_manager = APIManager()
        self.settings_file = os.path.join(get_app_root(), "settings.json")
        self.app_settings = self.load_settings()
        
        # システム・マネージャーの初期化
        self.reminder_manager = ReminderManager()
        self.reminder_manager.notify_signal.connect(self.show_notification)
        
        # SkillManagerにself(MainWindow)を渡すことで、プラグインからUI操作を可能にする
        self.skill_manager = SkillManager(context=self)
        self.llm_client = LLMClient(self.api_manager, lambda: self.app_settings, skill_manager=self.skill_manager)
        
        # 状態管理
        self.use_full_chat = self.app_settings.get("use_full_chat", False)
        self.is_chat_visible = False
        self.is_dragging = False
        self.old_pos = None
        
        # タイマー設定
        self.soliloquy_timer = QTimer(self)
        self.soliloquy_timer.timeout.connect(self.trigger_soliloquy)
        self.update_soliloquy_timer()
        
        self.initUI()

    def initUI(self):
        self.setWindowTitle("デスクトップAI")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAcceptDrops(True)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 各UIコンポーネントの構築
        self._setup_bubble_ui()
        self._setup_character_ui()
        self._setup_simple_input_ui()
        self._setup_full_chat_ui()
        
        self.adjustSize()

    def _setup_bubble_ui(self):
        self.bubble_label = QLabel("こんにちは！")
        self.bubble_label.setWordWrap(True)
        self.bubble_label.setStyleSheet("""
            QLabel {
                background-color: white; border: 2px solid #808080;
                border-radius: 15px; padding: 10px; font-size: 14px; color: black;
            }
        """)
        self.bubble_label.setVisible(False)
        self.layout.addWidget(self.bubble_label, alignment=Qt.AlignCenter)

    def _setup_character_ui(self):
        self.image_label = QLabel(self)
        self.update_character_image()
        self.layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

    def _setup_simple_input_ui(self):
        self.simple_input = QLineEdit()
        self.simple_input.setPlaceholderText("メッセージを入力...")
        self.simple_input.setStyleSheet("QLineEdit { background: white; border-radius: 10px; padding: 8px; color: black; }")
        self.simple_input.setVisible(False)
        self.simple_input.returnPressed.connect(self._handle_simple_submit)
        self.layout.addWidget(self.simple_input)

    def _setup_full_chat_ui(self):
        self.chat_widget = QWidget()
        chat_layout = QVBoxLayout(self.chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chat_history = QTextBrowser()
        self.chat_history.setStyleSheet("QTextBrowser { background: white; border-radius: 10px; color: black; }")
        self.chat_history.setFixedHeight(150)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("メッセージを入力... (Enterで送信)")
        self.chat_input.returnPressed.connect(self._handle_full_submit)
        
        chat_layout.addWidget(self.chat_history)
        chat_layout.addWidget(self.chat_input)
        self.chat_widget.setVisible(False)
        self.layout.addWidget(self.chat_widget)

    # --- チャット送信・レスポンス処理 ---
    
    def _handle_simple_submit(self):
        text = self.simple_input.text().strip()
        if text:
            self._start_chat_task(text)
            self.simple_input.clear()
            self.simple_input.setEnabled(False)
            self.bubble_label.setText("<i>思考中...</i>")
            self.bubble_label.setVisible(True)

    def _handle_full_submit(self):
        text = self.chat_input.text().strip()
        if text:
            self.chat_history.append(f"<b>あなた:</b> {text}")
            self._start_chat_task(text)
            self.chat_input.clear()
            self.chat_input.setEnabled(False)

    def _start_chat_task(self, text, image_path=None):
        self.update_soliloquy_timer() # タイマーリセット
        
        # 既存のスレッドがあれば停止（簡易的）
        if hasattr(self, "chat_thread") and self.chat_thread.isRunning():
            print("[System] Cancelling previous chat thread.")
            # 停止処理は複雑なため、ここでは上書き
        
        self.chat_thread = ChatThread(self.llm_client, text, image_path)
        self.chat_thread.response_ready.connect(self._on_chat_response)
        self.chat_thread.start()

    def _on_chat_response(self, response):
        if self.use_full_chat:
            self.chat_history.append(f"<b>AI:</b> {response}")
            self.chat_input.setEnabled(True)
            self.chat_input.setFocus()
        else:
            self.bubble_label.setText(response)
            self.bubble_label.setVisible(True)
            self.simple_input.setEnabled(True)
            self.simple_input.setFocus()
            self._stabilized_adjust_size()
            
            timeout = self.app_settings.get("bubble_timeout", 10) * 1000
            QTimer.singleShot(timeout, self.hide_bubble)

    # --- 設定・ファイル操作 ---

    def load_settings(self):
        defaults = {
            "gemini_model": "gemini-1.5-flash", "groq_model": "llama-3.3-70b-versatile",
            "active_api": "Gemini", "use_full_chat": False, "soliloquy_enabled": False,
            "soliloquy_interval": 30, "bubble_timeout": 10, "char_image": "",
            "char_size": 150,
            "system_prompt": "あなたはデスクトップAIペットです。"
        }
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # APIキー反映
                    for key in ["gemini_key", "groq_key"]:
                        if loaded.get(key): getattr(self.api_manager, f"set_{key}")(loaded[key])
                    return {**defaults, **loaded}
            except: pass
        return defaults

    def save_settings_to_file(self):
        try:
            self.app_settings["use_full_chat"] = self.use_full_chat
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.app_settings, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"Save error: {e}")

    def on_settings_saved(self, settings):
        self.app_settings = settings
        self.use_full_chat = settings.get("use_full_chat", False)
        self.update_character_image()
        self.update_soliloquy_timer()
        self.save_settings_to_file()

    def handle_dropped_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']:
            if self.llm_client.is_vision_supported():
                self._start_chat_task("この画像について教えてください。", path)
            else:
                self.show_notification("現在のモデルは画像認識に対応していません。")
        else:
            try:
                content = ""
                for enc in ['utf-8', 'cp932', 'euc-jp']:
                    try:
                        with open(path, 'r', encoding=enc) as f:
                            content = f.read(10000)
                            break
                    except: continue
                if not content: raise ValueError("Empty or binary file.")
                self._start_chat_task(f"以下のファイルを解析して要約してください。\n\nファイル名: {os.path.basename(path)}\n内容:\n{content}")
            except Exception as e: self.show_notification(f"読み込み失敗: {str(e)}")

    def _stabilized_adjust_size(self):
        """ウィンドウサイズ変更時にキャラクター（画像）の位置を1ピクセルも動かさない"""
        # 1. 変更前の「画像ラベルの中心」のグローバル座標を取得
        # まだUIが表示されていない場合はスキップ
        if not self.image_label.isVisible():
            self.adjustSize()
            return

        old_global_center = self.image_label.mapToGlobal(self.image_label.rect().center())

        # 2. サイズ調整実行
        self.adjustSize()
        
        # 3. 調整後の「画像ラベルの新しい中心」のグローバル座標を取得
        # (この時点ではウィンドウの位置は変わっていないので、ローカルな中心位置のズレを確認する)
        new_local_center = self.image_label.rect().center()
        new_global_center = self.image_label.mapToGlobal(new_local_center)
        
        # 4. ズレた分だけウィンドウを逆方向に移動
        diff = old_global_center - new_global_center
        self.move(self.pos() + diff)

    def show_notification(self, message):
        self.bubble_label.setText(message)
        self.bubble_label.setVisible(True)
        self._stabilized_adjust_size()
        QTimer.singleShot(self.app_settings.get("bubble_timeout", 10)*1000, self.hide_bubble)

    def hide_bubble(self):
        self.bubble_label.setVisible(False)
        self._stabilized_adjust_size()

    def update_character_image(self, override_path=None):
        path = override_path if override_path else self.app_settings.get("char_image", "")
        size = self.app_settings.get("char_size", 150)
        
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return
        # デフォルト（丸いアイコン）
        canvas = QPixmap(size, size)
        canvas.fill(Qt.transparent)
        painter = QPainter(canvas)
        painter.setBrush(QColor("#4A90E2"))
        painter.drawEllipse(5, 5, size-10, size-10)
        painter.end()
        self.image_label.setPixmap(canvas)

    def update_soliloquy_timer(self):
        enabled = self.app_settings.get("soliloquy_enabled", False)
        interval = self.app_settings.get("soliloquy_interval", 30)
        if enabled: self.soliloquy_timer.start(interval * 60 * 1000)
        else: self.soliloquy_timer.stop()

    def trigger_soliloquy(self):
        if hasattr(self, "chat_thread") and self.chat_thread.isRunning(): return
        prompt = "あなたはデスクトップAIペットです。今、ふと思ったことなどを1、2文で短くつぶやいてください。"
        self.chat_thread = ChatThread(self.llm_client, prompt)
        self.chat_thread.response_ready.connect(self._on_chat_response)
        self.chat_thread.start()

    # --- マウス・ウィンドウ操作 ---

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.old_pos)
            if delta.manhattanLength() > 5:
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self.old_pos = event.globalPos()
                self.is_dragging = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and not self.is_dragging:
            self.toggle_chat()

    def toggle_chat(self):
        self.is_chat_visible = not self.is_chat_visible
        if self.use_full_chat:
            self.chat_widget.setVisible(self.is_chat_visible)
            if self.is_chat_visible: self.chat_input.setFocus()
        else:
            self.simple_input.setVisible(self.is_chat_visible)
            if self.is_chat_visible: self.simple_input.setFocus()
        self._stabilized_adjust_size()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls: self.handle_dropped_file(urls[0].toLocalFile())

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("フルチャット" if not self.use_full_chat else "吹き出し", lambda: setattr(self, 'use_full_chat', not self.use_full_chat))
        menu.addAction("設定", self.open_settings)
        menu.addAction("データフォルダを開く", self.open_data_folder)
        menu.addAction("終了", QApplication.quit)
        menu.exec_(self.mapToGlobal(event.pos()))

    def open_data_folder(self):
        """プラグインやDBが保存されているフォルダをエクスプローラーで開く"""
        base_dir = get_app_root()
        if sys.platform == "linux":
            subprocess.run(["xdg-open", base_dir])
        elif sys.platform == "win32":
            os.startfile(base_dir)
        elif sys.platform == "darwin":
            subprocess.run(["open", base_dir])

    def open_settings(self):
        dialog = SettingsDialog(self.api_manager, self.app_settings, self)
        dialog.settings_saved.connect(self.on_settings_saved)
        dialog.exec_()
