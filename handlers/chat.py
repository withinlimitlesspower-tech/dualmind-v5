import httpx
import re
from config import DEEPSEEK_API_KEY

async def deepseek_chat(message: str, session_id: int = None) -> str:
    """Call DeepSeek API and return response text."""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.7
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: {str(e)}"

def detect_intent(message: str) -> str:
    """Detect intent from user message."""
    code_keywords = ["code", "function", "class", "implement", "write a program", "generate"]
    github_keywords = ["push", "github", "repository", "repo"]
    
    msg_lower = message.lower()
    
    if any(kw in msg_lower for kw in github_keywords):
        return "GITHUB_PUSH"
    elif any(kw in msg_lower for kw in code_keywords):
        return "CODE_GENERATE"
    else:
        return "GENERAL_CHAT"

def generate_code(text: str) -> str:
    """Extract code blocks from AI response."""
    # Find code blocks between triple backticks
    pattern = r"```(?:python)?\s*([\s\S]*?)```"
    matches = re.findall(pattern, text)
    if matches:
        return "\n".join(matches)
    # If no backticks, return the entire text as code
    return text.strip()
