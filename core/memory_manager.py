import os
import chromadb
from chromadb.utils import embedding_functions
from core.path_utils import get_data_path

class MemoryManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = get_data_path("memory_db")
            
        self.client = chromadb.PersistentClient(path=db_path)
        # デフォルトの埋め込み関数（sentence-transformersを使用）
        # 初回実行時にモデルがダウンロードされる可能性があります
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="conversation_history",
            embedding_function=self.ef
        )

    def add_memory(self, user_text, ai_response):
        """会話のペアを記憶に保存 (挨拶などは除外)"""
        # フィルタリング: 短すぎるメッセージや定型文は保存しない
        if len(user_text) < 4:
            return
            
        greetings = ["こんにちは", "おはよう", "こんばんは", "おやすみ", "ありがとう", "助かる", "お疲れ", "hello", "hi", "thanks"]
        if any(g in user_text.lower() for g in greetings) and len(user_text) < 10:
            print(f"[Memory] Skipped trivial memory: {user_text}")
            return

        combined_text = f"User: {user_text}\nAI: {ai_response}"
        # IDとしてタイムスタンプを使用
        import time
        doc_id = f"mem_{int(time.time() * 1000)}"
        
        self.collection.add(
            documents=[combined_text],
            metadatas=[{"timestamp": time.time(), "type": "chat"}],
            ids=[doc_id]
        )
        print(f"[Memory] Saved new memory: {doc_id}")

    def search_memories(self, query, n_results=3):
        """クエリに関連する過去の記憶を検索"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            memories = []
            if results and results['documents']:
                for doc_list in results['documents']:
                    memories.extend(doc_list)
            return memories
        except Exception as e:
            print(f"[Memory] Search error: {e}")
            return []
