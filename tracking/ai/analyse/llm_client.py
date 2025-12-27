
import os
from groq import Groq


from decouple import config

_client = None

def get_client():
    """Initialisation paresseuse du client Groq"""
    global _client
    if _client is None:
        _client = Groq(
            api_key=config("API_KEY_GROQ"),
        )
    return _client

def call_llm(prompt: str) -> str:
    client = get_client()
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5,  # plus stable pour du JSON
        max_completion_tokens=1024,
        top_p=1,
        stream=False
    )

    return completion.choices[0].message.content

