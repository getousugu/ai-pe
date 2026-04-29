import google.generativeai as genai
from groq import Groq
import json
import re
from datetime import datetime
from core.skill_manager import SkillManager
from core.memory_manager import MemoryManager

class LLMClient:
    def __init__(self, api_manager, settings_provider, skill_manager=None):
        self.api_manager = api_manager
        self.settings_provider = settings_provider
        self.skill_manager = skill_manager if skill_manager else SkillManager()
        self.memory_manager = MemoryManager() # 長期記憶マネージャー
        self.history = [] # チャット履歴を保持 (Groq用)
        self.gemini_chat = None # Geminiのチャットセッション保持用

    def is_vision_supported(self) -> bool:
        """現在のモデルが画像認識（マルチモーダル）に対応しているか判定"""
        settings = self.settings_provider()
        model_name = ""
        if settings.get("active_api") == "Gemini":
            model_name = settings.get("gemini_model", "")
        else:
            model_name = settings.get("groq_model", "")
        
        name = model_name.lower()
        return "gemini" in name or "vision" in name or "gemma-4" in name

    def generate_response(self, user_text: str, image_path: str = None) -> str:
        settings = self.settings_provider()
        active_api = settings.get("active_api")
        
        # TavilyのAPIキーを環境変数にセット (スキルで使用するため)
        if settings.get("tavily_key"):
            import os
            os.environ["TAVILY_API_KEY"] = settings["tavily_key"]
            
        # 現在の日時情報を付与
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_context = f"\n\n[現在時刻: {now}]"
        
        # 関連する過去の記憶を検索してコンテキストに追加
        past_memories = self.memory_manager.search_memories(user_text)
        memory_context = ""
        if past_memories:
            memory_context = "\n\n[関連する過去の記憶]:\n" + "\n---\n".join(past_memories)
        
        full_text = user_text + time_context + memory_context
        
        raw_response = ""
        if active_api == "Gemini":
            raw_response = self._generate_gemini(full_text, settings, image_path)
        elif active_api == "Groq":
            raw_response = self._generate_groq(full_text, settings)
        else:
            return "APIが設定されていません。右クリックから設定を開いてください。"
            
        final_response = self._strip_thoughts(raw_response)
        
        # 今回の会話を記憶に保存 (思考プロセスを除いた純粋な回答)
        if final_response and not final_response.startswith("Geminiエラー"):
            self.memory_manager.add_memory(user_text, final_response)
            
        return final_response

    def _strip_thoughts(self, text: str) -> str:
        """AIの思考プロセス（<thought>, <think>タグなど）を強力に隠す"""
        # タグ形式の削除 (<thought>, <think>, [thought], [think])
        # 閉じタグがない場合も考慮して、タグの開始から末尾までを消すパターンも追加
        patterns = [
            r'<thought>.*?</thought>',
            r'<think>.*?</think>',
            r'\[thought\].*?\[/thought\]',
            r'\[think\].*?\[/think\]',
            r'<thought>.*', # 閉じ忘れ対応
            r'<think>.*',    # 閉じ忘れ対応
            r'\[thought\].*',
            r'\[think\].*'
        ]
        for p in patterns:
            text = re.sub(p, '', text, flags=re.DOTALL | re.IGNORECASE)
            
        # 特定のキーワードで始まる思考行を削除
        lines = text.split('\n')
        filtered_lines = []
        for line in lines:
            # 「思考:」「Thinking:」「考え中:」などで始まる行をスキップ
            l_strip = line.lower().strip()
            if l_strip.startswith(('思考:', 'thinking:', '考え中:', 'thought:', 'think:')):
                continue
            filtered_lines.append(line)
            
        return '\n'.join(filtered_lines).strip()

    def _generate_gemini(self, text: str, settings: dict, image_path: str = None) -> str:
        model_name = settings.get("gemini_model")
        if not model_name or not self.api_manager.gemini_key:
            return "GeminiのAPIキーまたはモデルが設定されていません。"
        try:
            # スキルをToolとして取得
            tools_spec = self.skill_manager.get_all_specifications()
            gemini_tools = [{"function_declarations": tools_spec}] if tools_spec else None
            
            user_prompt = settings.get("system_prompt", "あなたはデスクトップAIペットです。")
            internal_instruction = """
【最重要ルール】
1. 思考プロセスや独り言を出力する場合は、必ず回答の冒頭で <thought>...</thought> タグを使用してその中に記述してください。
2. ユーザーへの直接的な回答は、必ず <thought> タグの外側（後ろ）に記述してください。
3. タグのない独り言や思考プロセスは、ユーザーを混乱させるため絶対に禁止します。
4. 最終的な回答は、有能な秘書のように簡潔かつ丁寧に行ってください。
"""
            full_instruction = f"{user_prompt}\n\n{internal_instruction}"
            
            model = genai.GenerativeModel(
                model_name, 
                tools=gemini_tools,
                system_instruction=full_instruction
            )
            
            # セッションがなければ作成
            if not self.gemini_chat or settings.get("last_model") != model_name:
                self.gemini_chat = model.start_chat(history=[])
                settings["last_model"] = model_name
            
            content = [text]
            if image_path and self.is_vision_supported():
                try:
                    from PIL import Image
                    img = Image.open(image_path)
                    content.append(img)
                    print(f"[LLM] Attached image: {image_path}")
                except Exception as e:
                    print(f"Failed to load image: {e}")

            response = self.gemini_chat.send_message(content)
            
            # 手動でFunction Callのループを回す
            for _ in range(5):
                if not response.candidates:
                    break
                
                # そのターンの全てのパーツを確認し、function_callを探す
                parts = response.candidates[0].content.parts
                fcs = [p.function_call for p in parts if p.function_call]
                
                if not fcs:
                    break
                
                # 全てのツール実行要求を処理
                tool_responses = []
                for fc in fcs:
                    args = {k: v for k, v in fc.args.items()}
                    result = self.skill_manager.execute_skill(fc.name, args)
                    tool_responses.append({
                        "function_response": {
                            "name": fc.name,
                            "response": {"result": result}
                        }
                    })
                
                # 実行結果を一括で返して次のターンへ
                response = self.gemini_chat.send_message(tool_responses)
            
            if response.candidates:
                # .text プロパティは function_call が混ざっていると ValueError を出すため、
                # 手動でテキストパーツのみを抽出する
                final_text = ""
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "text") and part.text:
                        final_text += part.text
                
                # もしテキストが空で、かつまだ function_call が残っている場合は
                # (ループ上限などで) 異常終了とみなす
                if not final_text and response.candidates[0].content.parts[0].function_call:
                    return "AIがツールを実行しようとしましたが、応答を完了できませんでした。"
                
                return final_text
            else:
                return "AIからの応答が空です。"
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Geminiエラー: {str(e)}"

    def _generate_groq(self, text: str, settings: dict) -> str:
        model_name = settings.get("groq_model")
        if not model_name or not self.api_manager.groq_key:
            return "GroqのAPIキーまたはモデルが設定されていません。"
        try:
            client = Groq(api_key=self.api_manager.groq_key)
            tools = []
            for spec in self.skill_manager.get_all_specifications():
                tools.append({"type": "function", "function": spec})

            user_prompt = settings.get("system_prompt", "あなたはデスクトップAIペットです。")
            internal_instruction = """
【最重要ルール】
1. 思考プロセスや独り言を出力する場合は、必ず回答の冒頭で <thought>...</thought> タグを使用してその中に記述してください。
2. ユーザーへの直接的な回答は、必ず <thought> タグの外側（後ろ）に記述してください。
3. タグのない独り言や思考プロセスは、ユーザーを混乱させるため絶対に禁止します。
4. 最終的な回答は、有能な秘書のように簡潔かつ丁寧に行ってください。
"""
            full_instruction = f"{user_prompt}\n\n{internal_instruction}"
            
            # 履歴の管理 (最大10往復分保持)
            if not self.history:
                self.history = [{"role": "system", "content": full_instruction}]
            else:
                self.history[0] = {"role": "system", "content": full_instruction}
            
            self.history.append({"role": "user", "content": text})
            if len(self.history) > 21: # system + user*10 + assistant*10
                self.history = [self.history[0]] + self.history[-20:]

            response = client.chat.completions.create(
                model=model_name,
                messages=self.history,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )
            
            response_message = response.choices[0].message
            self.history.append(response_message) # 履歴に追加
            
            tool_calls = getattr(response_message, 'tool_calls', None)
            
            if tool_calls:
                messages.append(response_message)
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    function_response = self.skill_manager.execute_skill(function_name, function_args)
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    })
                
                # 実行結果を含めて再度リクエスト
                second_response = client.chat.completions.create(
                    model=model_name,
                    messages=self.history
                )
                final_message = second_response.choices[0].message
                self.history.append(final_message) # 最終回答を履歴に追加
                return final_message.content
            
            return response_message.content
        except Exception as e:
            return f"Groqエラー: {str(e)}"
