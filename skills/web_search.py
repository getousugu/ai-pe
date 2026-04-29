from duckduckgo_search import DDGS
from skills.skill_base import BaseSkill

class WebSearchSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "web_search"

    def get_specification(self) -> dict:
        return {
            "name": "web_search",
            "description": "最新の情報やニュース、一般的な知識をインターネットで検索します。ユーザーが知らない情報を求めている時に使用してください。",
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
        try:
            print(f"[Skill] Searching for: {query}")
            with DDGS() as ddgs:
                # 検索結果を取得 (タイムアウト対策も兼ねて少し少なめにする)
                results = list(ddgs.text(query, max_results=5))
                
                if not results:
                    print("[Skill] No results found.")
                    return "検索結果が見つかりませんでした。別のキーワードで試すか、より具体的な情報を教えてください。"
                
                formatted_results = []
                for i, r in enumerate(results, 1):
                    title = r.get('title', '無題')
                    link = r.get('href', r.get('link', 'URLなし'))
                    snippet = r.get('body', r.get('snippet', '内容なし'))
                    formatted_results.append(f"資料{i}: {title}\nURL: {link}\n内容: {snippet}")
                
                output = "以下の検索結果を見つけました。これらに基づいて回答してください:\n\n" + "\n\n".join(formatted_results)
                print(f"[Skill] Successfully found {len(results)} results.")
                return output
        except Exception as e:
            return f"検索中にエラーが発生しました: {str(e)}"
