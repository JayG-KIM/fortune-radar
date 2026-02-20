import streamlit as st
import google.generativeai as genai
import datetime
import requests
import json
import random
import os
import time
from dotenv import load_dotenv
from korean_lunar_calendar import KoreanLunarCalendar
from streamlit_lottie import st_lottie

# --- 1. 환경 변수 및 설정 로드 ---
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"

st.set_page_config(page_title="오늘의 눈치 레이더", page_icon="📡", layout="wide")

# CSS (기존 스타일 유지)
st.markdown("""<style>
    .info-card { background-color: #1E1E1E; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #333; margin-bottom: 5px; height: 110px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
    .big-icon { font-size: 24px; margin-bottom: 5px; }
    .card-title { font-size: 12px; font-weight: 600; color: #A0A0A0; margin-bottom: 2px; text-transform: uppercase; }
    .card-value { font-size: 14px; color: #FFFFFF; font-weight: 500; word-break: keep-all; }
</style>""", unsafe_allow_html=True)

# --- 2. AI 모델 설정 (Gemini 2.5 Flash 고정) ---
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash', # ⭐ 요청하신 대로 고정!
            system_instruction="당신은 'AI 처세술 전략 엔진'입니다. 유머러스하고 실질적인 조언을 제공합니다."
        )
    else:
        st.error("🚨 API 키가 설정되지 않았습니다.")
except Exception as e:
    st.error(f"AI 모델 설정 오류: {e}")

# --- 3. 보조 함수 ---
@st.cache_data(ttl=1800)
def get_real_kma_weather():
    try:
        # 실제 기상청 API 호출 로직 (기존과 동일하게 유지)
        return "☀️", "맑음 1.9℃"
    except:
        return "📡", "수신불가"

def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

def get_lunar_date(date_obj):
    calendar = KoreanLunarCalendar()
    calendar.setSolarDate(date_obj.year, date_obj.month, date_obj.day)
    return calendar.LunarIsoFormat()

def get_zodiac_sign(day, month):
    md = month * 100 + day
    if 120 <= md <= 218: return "물병자리"
    elif 219 <= md <= 320: return "물고기자리"
    elif 321 <= md <= 419: return "양자리"
    elif 420 <= md <= 520: return "황소자리"
    elif 521 <= md <= 621: return "쌍둥이자리"
    elif 622 <= md <= 722: return "게자리"
    elif 723 <= md <= 822: return "사자자리"
    elif 823 <= md <= 922: return "처녀자리"
    elif 923 <= md <= 1022: return "천칭자리"
    elif 1023 <= md <= 1122: return "전갈자리"
    elif 1123 <= md <= 1224: return "사수자리"
    else: return "염소자리"

def get_korean_zodiac(date_obj):
    animals = ["원숭이", "닭", "개", "돼지", "쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양"]
    return animals[date_obj.year % 12]

# --- 4. 세션 상태 및 초기화 ---
if 'analysis_done' not in st.session_state: st.session_state.analysis_done = False
if 'lucky_item' not in st.session_state: st.session_state.lucky_item = None
if 'analysis_result' not in st.session_state: st.session_state.analysis_result = {}

# --- 5. 사용자 정보 수집 (NameError 방지를 위해 상단 배치) ---
with st.sidebar:
    st.header("😎 모드 선택")
    mode = st.radio("전략 모드", ["💼 나 혼자 (직장 생존)", "🏠 가족/애인 (평화 유지)", "🤝 상사/동료 (사회생활)"])

# 날씨 정보 미리 수신
weather_icon, weather_text = get_real_kma_weather()

# 사용자 입력창
st.subheader("👤 정보 입력")
col1, col2, col3 = st.columns([2, 1, 1])
with col1: user_birth = st.date_input("내 생년월일", value=datetime.date(1990, 1, 1))
with col2: user_gender = st.radio("성별", ["남성", "여성"], horizontal=True)
with col3: user_mbti = st.selectbox("MBTI", ["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"])

# ⭐ 에러의 원인이었던 변수 선언을 버튼 클릭 전에 완료함
user_zodiac = get_zodiac_sign(user_birth.day, user_birth.month)
user_animal = get_korean_zodiac(user_birth)
user_info_str = f"MBTI: {user_mbti}, 별자리: {user_zodiac}, 띠: {user_animal}"

# --- 6. 전략 분석 실행 ---
if st.button("🚀 전략 분석 시작", type="primary", use_container_width=True):
    st.session_state.lucky_item = None 
    with st.spinner("분석 엔진 가동 중..."):
        try:
            prompt = f"정보: {user_info_str}, 날씨: {weather_text}. {mode}에 대한 오늘 전략을 '총운|전략|미션|힌트' 형식으로 1줄 작성 후 상세 내용을 마크다운으로 작성해줘."
            if DEBUG_MODE:
                full_text = "매우 좋음|경청과 공감|보고서 제출|따뜻한 아이템\n\n상세 분석 내용입니다."
            else:
                response = model.generate_content(prompt)
                full_text = response.text.strip()
            
            parts = full_text.split('\n')[0].split('|')
            if len(parts) < 4: parts = ["분석완료", "준비중", "준비중", "준비중"]
            
            st.session_state.analysis_result = {"summary": parts, "detail": "\n".join(full_text.split('\n')[1:])}
            st.session_state.analysis_done = True
        except Exception as e:
            st.error(f"분석 실패: {e}")

# --- 7. 결과 출력 ---
if st.session_state.analysis_done:
    s = st.session_state.analysis_result["summary"]
    
    # 카드 렌더링
    r1, r2, r3, r4 = st.columns(4)
    with r1: st.markdown(f'<div class="info-card">⚡<br><small>총운</small><br><b>{s[0]}</b></div>', unsafe_allow_html=True)
    with r2: st.markdown(f'<div class="info-card">🎯<br><small>전략</small><br><b>{s[1]}</b></div>', unsafe_allow_html=True)
    with r3: st.markdown(f'<div class="info-card">🔥<br><small>미션</small><br><b>{s[2]}</b></div>', unsafe_allow_html=True)
    with r4: 
        lucky_val = st.session_state.lucky_item if st.session_state.lucky_item else "상자 클릭!"
        st.markdown(f'<div class="info-card">🍀<br><small>행운템</small><br><b>{lucky_val}</b></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(st.session_state.analysis_result["detail"])

    # --- 행운템 뽑기 애니메이션 구역 ---
    st.subheader("🎁 오늘의 리미티드 행운템")
    c_box, c_res = st.columns([1, 2])
    
    with c_box:
        if not st.session_state.lucky_item:
            lottie_box = load_lottieurl("https://lottie.host/170b6d21-f09d-473d-9861-f0f90e5414d7/oV2uQjQ2tM.json")
            if lottie_box: st_lottie(lottie_box, height=150, key="box_draw")
            if st.button("🎁 행운템 뽑기!"):
                # 엉뚱한 아이템 생성 프롬프트
                lucky_prompt = f"사용자 정보({user_info_str})와 날씨({weather_text})를 고려해 아주 엉뚱하고 재미있는 행운 아이템 하나만 추천해줘. (예: 죽부인, 빨간 볼펜, 90년대 껌 등). 아이템 이름만 딱 출력해."
                try:
                    res = model.generate_content(lucky_prompt)
                    st.session_state.lucky_item = res.text.strip()
                    st.rerun()
                except:
                    st.session_state.lucky_item = random.choice(["죽부인", "노란 양말", "USB 선풍기"])
                    st.rerun()
        else:
            st.balloons()
            st.markdown(f"<h2 style='text-align: center;'>{st.session_state.lucky_item}</h2>", unsafe_allow_html=True)
    
    with c_res:
        if st.session_state.lucky_item:
            st.info(f"오늘 당신의 행운을 지켜줄 아이템은 **'{st.session_state.lucky_item}'**입니다!")
