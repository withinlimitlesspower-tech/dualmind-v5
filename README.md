# AI Code Manager

AI-powered code generation and GitHub push tool.

## Setup

1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in your API keys.
6. Run the app: `uvicorn app:app --reload`
7. Open http://localhost:8000

## Features

- Chat with AI (DeepSeek)
- Generate code
- Push generated code to GitHub
- Session management

## Environment Variables

- `DEEPSEEK_API_KEY`: Your DeepSeek API key
- `GITHUB_TOKEN`: Your GitHub personal access token with repo permissions
