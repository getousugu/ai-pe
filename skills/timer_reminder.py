from skills.skill_base import BaseSkill

class TimerReminderSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "set_timer_reminder"

    def get_specification(self) -> dict:
        return {
            "name": "set_timer_reminder",
            "description": "タイマーやリマインダーを設定します。指定された秒数後にメッセージを表示します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "表示するメッセージ"
                    },
                    "seconds": {
                        "type": "integer",
                        "description": "何秒後に通知するか"
                    }
                },
                "required": ["message", "seconds"]
            }
        }

    def execute(self, message: str, seconds: int) -> str:
        if not hasattr(self, "context") or not self.context:
            return "エラー: リマインダー機能が初期化されていません。"
        
        # MainWindow経由でReminderManagerにアクセス
        return self.context.reminder_manager.set_reminder(message, seconds)
