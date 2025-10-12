from dotenv import dotenv_values
env_tokens = dotenv_values('.env')

API_KEY_TAVILY = env_tokens.get('API_KEY_TAVILY')