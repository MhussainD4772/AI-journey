import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["GOOGLE_API_KEY"]
MODEL = "gemini-3.5-flash-lite"
TEMPERATURE = 0.7
MAX_TOKENS = 1000
THINKING_LEVEL = "MINIMAL"