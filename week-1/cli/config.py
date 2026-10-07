import os
from pathlib import Path

from dotenv import load_dotenv

# config.py lives at <repo>/week-1/cli/config.py after the move, and at
# <repo>/cli/config.py before it. The .env file stays at the repo root.
_here = Path(__file__).resolve()
for _directory in _here.parents:
    _env = _directory / ".env"
    if _env.exists():
        load_dotenv(_env)
        break
else:
    load_dotenv()

API_KEY = os.environ["GOOGLE_API_KEY"]
MODEL = "gemini-3.5-flash-lite"
TEMPERATURE = 0.7
MAX_TOKENS = 1000
THINKING_LEVEL = "MINIMAL"