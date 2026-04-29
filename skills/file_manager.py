import os
from skills.skill_base import BaseSkill

class FileManagerSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "file_manager"

    def get_specification(self) -> dict:
        return {
            "name": "file_manager",
            "description": "ワークスペース内でファイルの作成（書き込み）や読み込みを行います。",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["write", "read"],
                        "description": "実行する操作（write: 書き込み, read: 読み込み）"
                    },
                    "filename": {
                        "type": "string",
                        "description": "ファイル名 (例: memo.txt)"
                    },
                    "content": {
                        "type": "string",
                        "description": "書き込む内容 (operationがwriteの場合に指定)"
                    }
                },
                "required": ["operation", "filename"]
            }
        }

    def execute(self, operation: str, filename: str, content: str = "") -> str:
        # このスクリプトの親の親にある workspace ディレクトリを指す
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        workspace_dir = os.path.join(base_dir, "workspace")
        
        if not os.path.exists(workspace_dir):
            os.makedirs(workspace_dir)
            
        file_path = os.path.join(workspace_dir, filename)
        
        # セキュリティチェック: ワークスペース外へのアクセスを禁止
        if not os.path.abspath(file_path).startswith(os.path.abspath(workspace_dir)):
            return "エラー: セキュリティのため、ワークスペース外のファイル操作は禁止されています。"

        try:
            if operation == "write":
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"ファイル '{filename}' を保存しました。"
            elif operation == "read":
                if not os.path.exists(file_path):
                    return f"エラー: ファイル '{filename}' が存在しません。"
                with open(file_path, "r", encoding="utf-8") as f:
                    data = f.read()
                return f"ファイル '{filename}' の内容:\n{data}"
            else:
                return "エラー: 不明な操作です。"
        except Exception as e:
            return f"ファイル操作中にエラーが発生しました: {str(e)}"
