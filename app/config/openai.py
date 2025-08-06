import os
from openai import OpenAI
from dotenv import load_dotenv
from app.config.db import supabase

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))