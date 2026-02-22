import google.generativeai as genai

# 4번째 줄: 따옴표 안에 'AIza'로 시작하는 키만 딱 들어가야 합니다.
GOOGLE_API_KEY = "AIzaSyAMGhVsXFWcmmFkOfGn8XThqvGmQ9fSJCo"

genai.configure(api_key=GOOGLE_API_KEY)

print("--- 내 API 키로 사용할 수 있는 모델 목록 ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"에러가 났습니다: {e}")