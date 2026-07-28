import os
# set your OPENAI_API_BASE, OPENAI_API_KEY here!
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_TYPE = os.getenv("OPENAI_API_TYPE", "open_ai")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
_max_tokens = os.getenv("MAX_TOKENS")
MAX_TOKENS = int(_max_tokens) if _max_tokens else None

import openai
openai.api_base = OPENAI_API_BASE
openai.api_key = OPENAI_API_KEY
openai.api_type = OPENAI_API_TYPE

# MODEL_NAME = "GPT-4o"  # GPT-4o
# MODEL_NAME = 'gpt-4-1106-preview' # 128k 
# MODEL_NAME = 'gpt-3.5-turbo'
# MODEL_NAME = 'gpt-4-32k' # 0613
# MODEL_NAME = 'gpt-4' # 0613
# MODEL_NAME = 'gpt-3.5-turbo' # 0613
# MODEL_NAME = 'gpt-4o-mini'