import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

response = client.chat.completions.create(
    model=os.getenv("LLM_MODEL", "gemini-2.5-flash"),
    messages=[
        {"role": "user", "content": "In one sentence, what is a database connection pool?"}
    ],
)
print(response.choices[0].message.content)