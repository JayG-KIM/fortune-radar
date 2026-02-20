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

# --- 1. 환경 변수 및 설정 로드 ---
load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    st.error("🚨 API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    st.stop()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"

st.set_page_config(page_title="오늘의 눈치 레이더", page_icon="📡", layout="wide")

# CSS: 원본 스타일 유지 (카드 높이 최적화)
st.markdown("""
<style>
    .info-card {
        background-color: #1E1E1E; padding: 10px; border-radius: 8px; text-align: center;
        border: 1px solid #333; margin-bottom: 5px; height: 120px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
    }
    .big-icon { font-size: 24px; margin-bottom: 5px; }
    .card-title { font-size: 12px; font-weight: 600; color: #A0A0A0; margin-bottom: 2px; text-transform: uppercase; }
    .card-value { font-size: 14px; color: #FFFFFF; font-weight: 500; word-break: keep-all; }
    .title-container { text-align: left; margin-bottom: 10px; }
    .main-title { font-size: 28px; font-weight: bold; color: #FFFFFF; margin-bottom: 5px; line-height: 1.2; }
    .sub-title { font-size: 14px; color: #CCCCCC; margin-bottom: 5px; line-height: 1.5; }
    .highlight { color: #00D4FF; font-weight: bold; }
    .weather-badge { background-color: #333; color: #fff; padding: 5px 10px; border-radius: 15px; font-size: 12px; margin-left: 10px; vertical-align: middle; }
    .engine-tag { display: inline-block; font-size: 11px; color: #00D4FF; border: 1px solid #00D4FF; padding: 4px 10px; border-radius: 15px; background-color: rgba(0, 212, 255, 0.05); margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 2. AI 모델 설정 (Gemini 2.5 Flash) ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction="당신은 'AI 처세술 전략 엔진'입니다. 전략은 짧은 키워드와 상세한 마크다운 설명으로 구분하여 제공합니다."
    )
except Exception as e:
    st.error(f"System Error: {e}")

# --- 3. 데이터 및 함수 (띠 로직 복구) ---
ZODIAC_ICONS = {"물병자리": "🏺", "물고기자리": "🐟", "양자리": "🐏", "황소자리": "🐂", "쌍둥이자리": "👯", "게자리": "🦀", "사자자리": "🦁", "처녀자리": "🧚", "천칭자리": "⚖️", "전갈자리": "🦂", "사수자리": "🏹", "염소자리": "🐐"}
ANIMAL_ICONS = {"쥐": "🐭", "소": "🐮", "호랑이": "🐯", "토끼": "🐰", "용": "🐲", "뱀": "🐍", "말": "🐴", "양": "🐑", "원숭이": "🐵", "닭": "🐔", "개": "🐶", "돼지": "🐷"}

@st.cache_data(ttl=1800)
def get_real_kma_weather():
    try:
        nx, ny = 58, 126
        base_date = datetime.datetime.now().strftime("%Y%m%d")
        base_time = (datetime.datetime.now() - datetime.timedelta(minutes=40)).strftime("%H00")
        url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
        params = {"serviceKey": WEATHER_API_KEY, "dataType": "JSON", "base_date": base_date, "base_time": base_time, "nx": nx, "ny": ny}
        res = requests.get(url, params=params, timeout=3).json()
        items = res['response']['body']['items']['item']
        data = {i['category']: i['obsrValue'] for i in items}
        pty, temp = int(data.get('PTY', 0)), data.get('T1H', '?')
        icon = "☀️" if pty == 0 else "☔" if pty in [1, 5] else "🌨️"
        return icon, f"{temp}℃"
    except: return "📡", "수신불가"

def get_lunar_date(date_obj):
    cal = KoreanLunarCalendar()
    cal.setSolarDate(date_obj.year, date_obj.month, date_obj.day)
    return cal.LunarIsoFormat()

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

def get_ipchun_date(year):
    if year in [2021, 2025]: return datetime.date(year, 2, 3)
    if 1920 <= year <= 1984 and (year % 4 == 0): return datetime.date(year, 2, 5)
    return datetime.date(year, 2, 4)

def get_korean_zodiac(date_obj):
    year = date_obj.year
    target_year = year if date_obj >= get_ipchun_date(year) else year - 1
    animals = ["원숭이", "닭", "개", "돼지", "쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양"]
    return animals[target_year % 12]

def display_card(column, icon, title, value):
    with column:
        st.markdown(f'<div class="info-card"><div class="big-icon">{icon}</div><div class="card-title">{title}</div><div class="card-value">{value}</div></div>', unsafe_allow_html=True)

# --- 4. 메인 UI ---
with st.sidebar:
    st.header("😎 모드 선택")
    mode = st.radio("전략 모드", ["💼 나 혼자 (직장 생존)", "🏠 가족/애인 (평화 유지)", "🤝 상사/동료 (사회생활)"], index=0)

weather_icon, weather_text = get_real_kma_weather()
subtitle_text = "데이터로 분석한 <span class='highlight'>오늘의 직장 생존 전략</span>"
weather_html = "" if "나 혼자" in mode else f"<span class='weather-badge'>{weather_icon} 마곡 {weather_text}</span>"

if "가족" in mode: subtitle_text = "평화로운 관계를 위한 <span class='highlight'>로맨스/가족 전략</span>"
elif "상사" in mode: subtitle_text = "성공적인 사회생활을 위한 <span class='highlight'>관계 공략법</span>"

st.markdown(f'<div class="title-container"><span class="main-title">오늘의 눈치 레이더</span>{weather_html}<div class="sub-title">{subtitle_text}</div><div class="engine-tag">Powered by AI Work Strategy Engine</div></div><hr style="border-top: 1px solid #333; margin-top: 5px; margin-bottom: 15px;">', unsafe_allow_html=True)

mbti_list = ["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"]
user_birth, target_birth, target_mbti = None, None, "정보 없음"

if "나 혼자" in mode:
    st.subheader("👤 내 정보")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: user_birth = st.date_input("내 생년월일", value=datetime.date(1990, 1, 1), min_value=datetime.date(1920, 1, 1))
    with c2: user_gender = st.radio("내 성별", ["남성", "여성"], horizontal=True)
    with c3: user_mbti = st.selectbox("내 MBTI", mbti_list)
else:
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("👤 나 (User)")
        user_birth = st.date_input("내 생년월일", value=datetime.date(1990, 1, 1), min_value=datetime.date(1920, 1, 1))
        r1, r2 = st.columns(2)
        with r1: user_gender = st.radio("내 성별", ["남성", "여성"])
        with r2: user_mbti = st.selectbox("내 MBTI", mbti_list)
    with col_r:
        label = "🏠 가족/애인" if "가족" in mode else "🤝 상사/동료"
        st.subheader(f"{label} (Target)")
        target_birth = st.date_input("상대 생년월일", value=datetime.date(1990, 1, 1))
        r1, r2 = st.columns(2)
        with r1: target_gender = st.radio("상대 성별", ["남성", "여성"])
        with r2: target_mbti = st.selectbox("상대 MBTI", ["모름"] + mbti_list)

# 카드 데이터 계산 및 출력
u_l, u_z, u_a = get_lunar_date(user_birth), get_zodiac_sign(user_birth.day, user_birth.month), get_korean_zodiac(user_birth)
if "나 혼자" in mode:
    c1, c2, c3, c4 = st.columns(4)
    display_card(c1, ZODIAC_ICONS.get(u_z), "내 별자리", u_z)
    display_card(c2, ANIMAL_ICONS.get(u_a), "내 띠", f"{u_a}띠")
    display_card(c3, "🌕", "음력 생일", u_l)
    display_card(c4, weather_icon, "마곡 날씨", weather_text)
else:
    t_l, t_z, t_a = get_lunar_date(target_birth), get_zodiac_sign(target_birth.day, target_birth.month), get_korean_zodiac(target_birth)
    cl, cr = st.columns(2)
    with cl:
        sc1, sc2, sc3 = st.columns(3)
        display_card(sc1, ZODIAC_ICONS.get(u_z), "별자리", u_z); display_card(sc2, ANIMAL_ICONS.get(u_a), "띠", f"{u_a}띠"); display_card(sc3, "🌕", "음력", u_l)
    with cr:
        sc1, sc2, sc3 = st.columns(3)
        display_card(sc1, ZODIAC_ICONS.get(t_z), "별자리", t_z); display_card(sc2, ANIMAL_ICONS.get(t_a), "띠", f"{t_a}띠"); display_card(sc3, "🌕", "음력", t_l)

st.write("")
st.markdown("---")

# --- 5. 분석 로직 (프롬프트 핵심 수정) ---
btn_label = "🚀 전략 분석 시작"
if "가족" in mode: btn_label = "💕 평화/사랑 전략 수립"
elif "상사" in mode: btn_label = "🤝 사회생활 공략법 분석"

if st.button(btn_label, type="primary", use_container_width=True):
    with st.spinner("분석 중..."):
        # 1. 행운템 다양성 보장 가이드
        # 2. 첫 줄 키워드와 본문 분석 텍스트의 엄격한 분리 요청
        lucky_guide = "Lucky Item (KEYWORD4) must be a quirky physical object like 'Bamboo wife(죽부인)', 'Vintage metronome', 'Red socks'. Avoid drinks."
        prompt = f"""
        [Output Format]
        Line 1: KEYWORD1|KEYWORD2|KEYWORD3|KEYWORD4 (Exactly 4 short keywords)
        Line 2+: Detailed markdown analysis (Bullets allowed)
        
        [Data] Mode:{mode}, Weather:{weather_text}, User:{user_mbti}/{u_z}/{u_a}. {lucky_guide}
        """
        try:
            response = model.generate_content(prompt).text.strip()
            lines = response.split('\n')
            parts = lines[0].split('|')
            detail_text = "\n".join(lines[1:]).strip()
            
            # 카드 출력 (요약만!)
            st.success("✅ 전략 수립 완료")
            t1, t2, t3, t4 = "총운", "관계", "미션", "행운템"
            r1, r2, r3, r4 = st.columns(4)
            display_card(r1, "⚡", t1, parts[0].strip())
            display_card(r2, "🎯", t2, parts[1].strip())
            display_card(r3, "🔥", t3, parts[2].strip())
            display_card(r4, "🍀", t4, parts[3].strip())
            
            # 상세 분석 출력 (카드 밖 하단!)
            st.markdown("---")
            st.markdown(detail_text)
            
# [공유하기 기능 부활]

st.markdown("---")
st.subheader("📋 친구에게 공유하기")
share_text = f"""[오늘의 눈치 레이더]
⚡ {t1}: {parts[0].strip()}
🎯 {t2}: {parts[1].strip()}
🔥 {t3}: {parts[2].strip()}
🍀 {t4}: {parts[3].strip()}

👉 전략 확인하기: https://nunchi-radar.streamlit.app"""

st.code(share_text, language="text")
st.caption("👆 위 박스 오른쪽의 '복사(Copy)' 아이콘을 누르면 결과가 복사됩니다!")

        except Exception as e:
            st.error("분석 실패. 다시 시도해 주세요.")

