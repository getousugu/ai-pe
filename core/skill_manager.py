import os
import sys
import importlib
import inspect
from skills.skill_base import BaseSkill
from core.path_utils import get_data_path, get_app_root

class SkillManager:
    def __init__(self, context=None):
        self.skills = {}
        self.context = context # ReminderManager などのインスタンスを保持
        self.load_skills()

    def load_skills(self):
        """標準スキル(skills)と外部プラグイン(plugins)の両方をロードする"""
        skills_dir = get_data_path("skills")
        plugins_dir = get_data_path("plugins")
        
        # 読み込み対象のディレクトリリスト
        target_dirs = [
            ("skills", skills_dir),
            ("plugins", plugins_dir)
        ]
        
        # import用パスの調整
        base_dir = get_app_root()
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)

        for prefix, directory in target_dirs:
            if not os.path.exists(directory):
                continue
                
            print(f"[SkillManager] Scanning {prefix} directory...")
            for filename in os.listdir(directory):
                if filename.endswith(".py") and not filename.startswith("__") and filename != "skill_base.py":
                    module_name = f"{prefix}.{filename[:-3]}"
                    self._load_module(module_name)

        print(f"[SkillManager] Total skills loaded: {len(self.skills)} ({', '.join(self.skills.keys())})")

    def _load_module(self, module_name):
        """モジュールを読み込み、BaseSkillを継承したクラスをインスタンス化して登録"""
        try:
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            module = importlib.import_module(module_name)
            
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseSkill) and obj is not BaseSkill:
                    skill_instance = obj()
                    skill_instance.set_context(self.context)
                    self.skills[skill_instance.name] = skill_instance
                    print(f"  - Loaded skill: {skill_instance.name} from {module_name}")
        except Exception as e:
            print(f"  - [Error] Failed to load {module_name}: {e}")

    def get_all_specifications(self):
        """全スキルの仕様（Gemini/Groq共通フォーマット）をリストで返す"""
        return [skill.get_specification() for skill in self.skills.values()]

    def execute_skill(self, name, arguments):
        """スキル名と引数を指定して実行"""
        if name in self.skills:
            print(f"Executing skill: {name} with args {arguments}")
            return self.skills[name].execute(**arguments)
        return f"エラー: スキル '{name}' が見つかりません。"
