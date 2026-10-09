import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


class LLMClient:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured."
            )

        self.model = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0,
            api_key=api_key,
        )

    def invoke(self, messages):
        return self.model.invoke(messages)