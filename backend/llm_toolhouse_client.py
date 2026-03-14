import os, json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from toolhouse import Toolhouse
from prompts import SYSTEM_PROMPT, JSON_OUTPUT_INSTRUCTION

# Load .env from backend dir, then frontend .env.local (so keys in frontend work when running backend)
_backend_dir = Path(__file__).resolve().parent
load_dotenv(_backend_dir / ".env")
load_dotenv(_backend_dir / ".." / "frontend" / ".env.local")

# Accept FEATHERLESS_API_KEY, OPENAI_API_KEY, or VITE_OPENAI_API_KEY (frontend .env.local)
_api_key = (
    os.getenv("FEATHERLESS_API_KEY")
    or os.getenv("OPENAI_API_KEY")
    or os.getenv("VITE_OPENAI_API_KEY")
)

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=_api_key
)

th = Toolhouse(
    api_key=os.getenv("TOOLHOUSE_API_KEY"),
    provider="openai"
)

MODEL=os.getenv("MODEL_NAME","meta-llama/Llama-3.1-8B-Instruct")

def run_agent(prompt):

    messages=[
        {"role":"system","content":SYSTEM_PROMPT + "\n\n" + JSON_OUTPUT_INSTRUCTION},
        {"role":"user","content":prompt}
    ]

    tools=th.get_tools()

    r=client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        temperature=0.1
    )

    tool_msgs=th.run_tools(r)

    if tool_msgs:
        messages+=tool_msgs
        r=client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            temperature=0.1
        )

    out=r.choices[0].message.content
    return json.loads(out)
