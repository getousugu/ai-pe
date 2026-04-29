from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QGroupBox, QMessageBox, QTextEdit, QFileDialog, QCheckBox, QSpinBox)
from PyQt5.QtCore import pyqtSignal
from core.api_manager import APIManager

class SettingsDialog(QDialog):
    settings_saved = pyqtSignal(dict)

    def __init__(self, api_manager: APIManager, current_settings: dict = None, parent=None):
        super().__init__(parent)
        self.api_manager = api_manager
        self.current_settings = current_settings or {}
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("設定")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # API設定セクション
        layout.addWidget(self._create_api_group("Gemini", self.current_settings.get("gemini_key", ""), self.current_settings.get("gemini_model", "")))
        layout.addWidget(self._create_api_group("Groq", self.current_settings.get("groq_key", ""), self.current_settings.get("groq_model", "")))
        
        # Tavily (検索API) 設定
        tavily_group = QGroupBox("Tavily Search API (任意)")
        t_layout = QVBoxLayout()
        self.tavily_key_input = QLineEdit(self.current_settings.get("tavily_key", ""))
        self.tavily_key_input.setPlaceholderText("Tavily API Key")
        self.tavily_key_input.setEchoMode(QLineEdit.Password)
        t_layout.addWidget(QLabel("WEB検索機能を有効にするためのキーです。"))
        t_layout.addWidget(self.tavily_key_input)
        tavily_group.setLayout(t_layout)
        layout.addWidget(tavily_group)

        # キャラクター・プロンプト設定
        layout.addWidget(self._create_character_group())
        
        # 自律動作設定
        layout.addWidget(self._create_soliloquy_group())

        # メインAPI選択
        active_api_layout = QHBoxLayout()
        active_api_layout.addWidget(QLabel("メインで使用するAPI:"))
        self.active_api_combo = QComboBox()
        self.active_api_combo.addItems(["Gemini", "Groq"])
        self.active_api_combo.setCurrentText(self.current_settings.get("active_api", "Gemini"))
        active_api_layout.addWidget(self.active_api_combo)
        layout.addLayout(active_api_layout)

        # 保存・キャンセルボタン
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _create_api_group(self, provider, key_val, model_val):
        group = QGroupBox(f"{provider} 設定")
        layout = QVBoxLayout()
        
        key_input = QLineEdit(key_val)
        key_input.setPlaceholderText(f"{provider} API Key")
        key_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel(f"{provider} APIキー:"))
        layout.addWidget(key_input)
        
        fetch_layout = QHBoxLayout()
        model_combo = QComboBox()
        if model_val: model_combo.addItem(model_val)
        
        fetch_btn = QPushButton("モデルを取得")
        fetch_btn.clicked.connect(lambda: self._fetch_models(provider, key_input, model_combo, fetch_btn))
        
        fetch_layout.addWidget(model_combo, 1)
        fetch_layout.addWidget(fetch_btn)
        layout.addLayout(fetch_layout)
        
        group.setLayout(layout)
        
        # 保存時に参照できるよう保持
        if provider == "Gemini":
            self.gemini_key_input, self.gemini_model_combo = key_input, model_combo
        else:
            self.groq_key_input, self.groq_model_combo = key_input, model_combo
            
        return group

    def _create_character_group(self):
        group = QGroupBox("キャラクター・プロンプト設定")
        layout = QVBoxLayout()
        
        self.prompt_input = QTextEdit(self.current_settings.get("system_prompt", "あなたはデスクトップAIペットです。"))
        self.prompt_input.setFixedHeight(80)
        layout.addWidget(QLabel("システムプロンプト:"))
        layout.addWidget(self.prompt_input)
        
        img_layout = QHBoxLayout()
        self.image_path_input = QLineEdit(self.current_settings.get("char_image", ""))
        browse_btn = QPushButton("参照")
        browse_btn.clicked.connect(self.browse_image)
        clear_btn = QPushButton("解除")
        clear_btn.clicked.connect(lambda: self.image_path_input.clear())
        
        img_layout.addWidget(self.image_path_input)
        img_layout.addWidget(browse_btn)
        img_layout.addWidget(clear_btn)
        layout.addWidget(QLabel("キャラクター画像パス:"))
        layout.addLayout(img_layout)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("表示サイズ（px）:"))
        self.char_size = QSpinBox()
        self.char_size.setRange(50, 800)
        self.char_size.setValue(self.current_settings.get("char_size", 150))
        size_layout.addWidget(self.char_size)
        layout.addLayout(size_layout)
        
        group.setLayout(layout)
        return group

    def _create_soliloquy_group(self):
        group = QGroupBox("自律動作・UI設定")
        layout = QVBoxLayout()
        
        self.soliloquy_enabled = QCheckBox("自発的なつぶやきを有効にする")
        self.soliloquy_enabled.setChecked(self.current_settings.get("soliloquy_enabled", False))
        layout.addWidget(self.soliloquy_enabled)
        
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("つぶやき間隔（分）:"))
        self.soliloquy_interval = QSpinBox()
        self.soliloquy_interval.setRange(1, 1440)
        self.soliloquy_interval.setValue(self.current_settings.get("soliloquy_interval", 30))
        interval_layout.addWidget(self.soliloquy_interval)
        layout.addLayout(interval_layout)

        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("吹き出し消去（秒）:"))
        self.bubble_timeout = QSpinBox()
        self.bubble_timeout.setRange(1, 3600)
        self.bubble_timeout.setValue(self.current_settings.get("bubble_timeout", 10))
        timeout_layout.addWidget(self.bubble_timeout)
        layout.addLayout(timeout_layout)
        
        group.setLayout(layout)
        return group

    def _fetch_models(self, provider, key_input, combo, btn):
        key = key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "エラー", "APIキーを入力してください。")
            return
        
        btn.setEnabled(False)
        btn.setText("取得中...")
        
        try:
            if provider == "Gemini":
                self.api_manager.set_gemini_key(key)
                models = self.api_manager.get_gemini_models()
            else:
                self.api_manager.set_groq_key(key)
                models = self.api_manager.get_groq_models()
                
            combo.clear()
            if models:
                combo.addItems(models)
                QMessageBox.information(self, "成功", f"{provider} のモデルを取得しました。")
            else:
                QMessageBox.warning(self, "失敗", "モデルを取得できませんでした。キーを確認してください。")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"通信エラー: {e}")
            
        btn.setEnabled(True)
        btn.setText("モデルを取得")

    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "画像を選択", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if file_path:
            self.image_path_input.setText(file_path)

    def save_settings(self):
        settings = {
            "gemini_key": self.gemini_key_input.text().strip(),
            "gemini_model": self.gemini_model_combo.currentText(),
            "groq_key": self.groq_key_input.text().strip(),
            "groq_model": self.groq_model_combo.currentText(),
            "tavily_key": self.tavily_key_input.text().strip(),
            "active_api": self.active_api_combo.currentText(),
            "system_prompt": self.prompt_input.toPlainText().strip(),
            "char_image": self.image_path_input.text().strip(),
            "char_size": self.char_size.value(),
            "soliloquy_enabled": self.soliloquy_enabled.isChecked(),
            "soliloquy_interval": self.soliloquy_interval.value(),
            "bubble_timeout": self.bubble_timeout.value()
        }
        self.settings_saved.emit(settings)
        self.accept()
