import os
from tavily import TavilyClient
from skills.skill_base import BaseSkill

class TavilySearchSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "tavily_search"

    def get_specification(self) -> dict:
        return {
            "name": "tavily_search",
            "description": "AI向けに最適化された高度なウェブ検索を実行します。通常のウェブ検索(web_search)よりも正確で要約された最新情報が得られるため、APIキーがある場合はこちらを優先してください。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "検索キーワード"
                    }
                },
                "required": ["query"]
            }
        }

    def execute(self, query: str) -> str:
        # LLMClientが設定から環境変数にセットすることを想定
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            return "エラー: TavilyのAPIキーが設定されていません。設定画面から入力してください。また、APIキーがない場合は通常の web_search を使用してください。"
            
        try:
            print(f"[Skill] Tavily searching for: {query}")
            client = TavilyClient(api_key=api_key)
            # search_depth="advanced" でより詳細な情報を取得
            response = client.search(query=query, search_depth="advanced", max_results=5)
            
            results = response.get('results', [])
            if not results:
                return "検索結果が見つかりませんでした。"
                
            formatted = []
            for i, r in enumerate(results, 1):
                title = r.get('title', '無題')
                url = r.get('url', 'URLなし')
                content = r.get('content', '内容なし')
                formatted.append(f"資料{i}: {title}\nURL: {url}\n内容: {content}")
            
            return "Tavilyによる高度な検索結果:\n\n" + "\n\n".join(formatted)
        except Exception as e:
            return f"Tavily検索中にエラーが発生しました: {str(e)}"
