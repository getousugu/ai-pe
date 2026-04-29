import subprocess
from skills.skill_base import BaseSkill

class SystemCommandSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "system_cmd"

    def get_specification(self) -> dict:
        return {
            "name": "system_cmd",
            "description": "Linuxのシステムコマンドを実行します。アプリケーションの起動（例: xed, firefox）、システム状態の確認（例: df -h, free -m）、ファイルの検索などに使用してください。ユーザーの指示に基づいて実行します。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "実行するシェルコマンド"
                    }
                },
                "required": ["command"]
            }
        }

    def execute(self, command: str) -> str:
        try:
            print(f"[Skill] Executing command: {command}")
            # 安全のためタイムアウトを設定
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=15
            )
            
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            
            if result.returncode == 0:
                return f"実行成功:\n{stdout if stdout else '出力なし'}"
            else:
                return f"実行失敗 (コード {result.returncode}):\n{stderr}"
        except subprocess.TimeoutExpired:
            return "エラー: コマンドの実行がタイムアウトしました。"
        except Exception as e:
            return f"エラー: {str(e)}"
