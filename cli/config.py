import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["GOOGLE_API_KEY"]
MODEL = "gemini-3.8-flash"
TEMPERATURE = 0.7
MAX_TOKENS = 1000