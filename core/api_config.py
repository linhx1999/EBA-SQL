import os
# set your OPENAI_API_BASE, OPENAI_API_KEY here!
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
import openai
openai.api_base = OPENAI_API_BASE
openai.api_key = OPENAI_API_KEY


# MODEL_NAME = "GPT-4o"  # GPT-4o
# MODEL_NAME = 'gpt-4-1106-preview' # 128k 
MODEL_NAME = 'gpt-3.5-turbo'
# MODEL_NAME = 'gpt-4-32k' # 0613
# MODEL_NAME = 'gpt-4' # 0613
# MODEL_NAME = 'gpt-3.5-turbo' # 0613
# MODEL_NAME = 'gpt-4o-mini'