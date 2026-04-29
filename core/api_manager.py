import os
import google.generativeai as genai
from groq import Groq

class APIManager:
    def __init__(self):
        self.gemini_key = ""
        self.groq_key = ""
        
    def set_gemini_key(self, key):
        self.gemini_key = key
        if key:
            genai.configure(api_key=key)
            
    def set_groq_key(self, key):
        self.groq_key = key

    def get_gemini_models(self):
        if not self.gemini_key:
            return []
        try:
            models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    models.append(m.name)
            return models
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return []

    def get_groq_models(self):
        if not self.groq_key:
            return []
        try:
            client = Groq(api_key=self.groq_key)
            models = client.models.list()
            return [m.id for m in models.data]
        except Exception as e:
            print(f"Groq API Error: {e}")
            return []
