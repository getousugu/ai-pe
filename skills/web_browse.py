import trafilatura
from skills.skill_base import BaseSkill

class WebBrowseSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "web_browse"

    def get_specification(self) -> dict:
        return {
            "name": "web_browse",
            "description": "指定されたURLのウェブページの内容（テキスト）を読み取ります。web_searchの結果からさらに詳しく知りたいページがある場合に使用してください。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "アクセスするURL"
                    }
                },
                "required": ["url"]
            }
        }

    def execute(self, url: str) -> str:
        try:
            print(f"[Skill] Browsing: {url}")
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return f"エラー: {url} から情報を取得できませんでした。"
            
            # 本文のみを抽出（広告やナビゲーションを除外）
            content = trafilatura.extract(downloaded)
            if not content:
                return f"エラー: {url} の内容を解析できませんでした。"
            
            # LLMのコンテキスト制限を考慮して、最大3000文字程度に制限
            if len(content) > 3000:
                content = content[:3000] + "\n\n(コンテンツが長いため、一部省略されました)"
                
            return f"--- URL: {url} の内容 ---\n\n{content}"
        except Exception as e:
            return f"ブラウジング中にエラーが発生しました: {str(e)}"
