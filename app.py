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

if not os.getenv("GEMINI_API_KEY"):
    st.error("🚨 API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    st.stop()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"

st.set_page_config(
    page_title="오늘의 눈치 레이더",
    page_icon="📡",
    layout="wide"
)

# --- 2. AI 모델 설정 ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction="당신은 'AI 처세술 전략 엔진'입니다. 사용자와 상대방의 기질, 환경(날씨)을 분석하여 구체적인 행동 전략을 제시합니다."
    )
except Exception as e:
    st.error(f"System Error: {e}")

# --- 3. CSS 스타일 ---
st.markdown("""
<style>
    .info-card {
        background-color: #1E1E1E; padding: 10px; border-radius: 8px; text-align: center;
        border: 1px solid #333; margin-bottom: 5px; height: 110px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
    }
    .big-icon { font-size: 24px; margin-bottom: 5px; }
    .card-title { font-size: 12px; font-weight: 600; color: #A0A0A0; margin-bottom: 2px; text-transform: uppercase; }
    .card-value { font-size: 14px; color: #FFFFFF; font-weight: 500; word-break: keep-all; }
    .highlight { color: #00D4FF; font-weight: bold; }
    .weather-badge { background-color: #333; color: #fff; padding: 5px 10px; border-radius: 15px; font-size: 12px; margin-left: 10px; vertical-align: middle; }
    .engine-tag { display: inline-block; font-size: 11px; color: #00D4FF; border: 1px solid #00D4FF; padding: 4px 10px; border-radius: 15px; background-color: rgba(0, 212, 255, 0.05); margin-top: 5px; }
    .quota-error { background-color: #2b1c1c; border: 1px solid #ff4b4b; color: #ffcccc; padding: 15px; border-radius: 8px; margin-top: 20px; font-size: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 4. 데이터 로직 함수 ---
@st.cache_data(ttl=1800)
def get_real_kma_weather():
    try:
        nx, ny = 58, 126
        base_date = datetime.datetime.now().strftime("%Y%m%d")
        base_time = (datetime.datetime.now() - datetime.timedelta(minutes=40)).strftime("%H00")
        url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
        params = {"serviceKey": WEATHER_API_KEY, "pageNo": "1", "numOfRows": "1000", "dataType": "JSON", "base_date": base_date, "base_time": base_time, "nx": nx, "ny": ny}
        response = requests.get(url, params=params, timeout=3)
        data = response.json()
        items = data['response']['body']['items']['item']
        weather_data = {item['category']: item['obsrValue'] for item in items}
        temp = weather_data.get('T1H', '?')
        return "☀️", f"맑음 {temp}℃"
    except: return "📡", "수신불가"

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

def display_card(column, icon, title, value):
    with column:
        st.markdown(f'<div class="info-card"><div class="big-icon">{icon}</div><div class="card-title">{title}</div><div class="card-value">{value}</div></div>', unsafe_allow_html=True)

def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- 5. 세션 상태 초기화 (화면 유지용) ---
if 'analysis_done' not in st.session_state: st.session_state.analysis_done = False
if 'lucky_item_revealed' not in st.session_state: st.session_state.lucky_item_revealed = False
if 'analysis_result' not in st.session_state: st.session_state.analysis_result = {}

# --- 6. 메인 레이아웃 ---
with st.sidebar:
    st.header("😎 모드 선택")
    mode = st.radio("전략 모드", ["💼 나 혼자 (직장 생존)", "🏠 가족/애인 (평화 유지)", "🤝 상사/동료 (사회생활)"], index=0)
    st.markdown("---")
    st.caption("Ver 2.5.0 (Interaction Pack)")

weather_icon, weather_text = get_real_kma_weather()

# 제목 섹션
weather_html = f"<span class='weather-badge'>{weather_icon} 마곡 {weather_text}</span>"
if "나 혼자" in mode:
    subtitle_text = "데이터로 분석한 <span class='highlight'>오늘의 직장 생존 전략</span>"
elif "가족" in mode:
    subtitle_text = "평화로운 관계를 위한 <span class='highlight'>로맨스/가족 전략</span>"
else:
    subtitle_text = "성공적인 사회생활을 위한 <span class='highlight'>관계 공략법</span>"

st.markdown(f'<div class="title-container"><span class="main-title">오늘의 눈치 레이더</span>{weather_html}<div class="sub-title">{subtitle_text}</div><div class="engine-tag">Powered by AI Work Strategy Engine</div></div><hr style="border-top: 1px solid #333; margin-top: 5px; margin-bottom: 15px;">', unsafe_allow_html=True)

# --- 입력 폼 ---
mbti_list = ["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"]

if "나 혼자" in mode:
    st.subheader("👤 내 정보")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: user_birth = st.date_input("내 생년월일", value=datetime.date(1990, 1, 1), min_value=datetime.date(1920, 1, 1))
    with c2: user_gender = st.radio("내 성별", ["남성", "여성"], horizontal=True)
    with c3: user_mbti = st.selectbox("내 MBTI", mbti_list)
    
    # 데이터 계산
    user_lunar = get_lunar_date(user_birth)
    user_zodiac = get_zodiac_sign(user_birth.day, user_birth.month)
    user_animal = get_korean_zodiac(user_birth)
    
    # 카드 출력 (복구됨)
    c1, c2, c3, c4 = st.columns(4)
    display_card(c1, "⭐", "내 별자리", user_zodiac)
    display_card(c2, "🐾", "내 띠", f"{user_animal}띠")
    display_card(c3, "🌕", "음력 생일", user_lunar)
    display_card(c4, weather_icon, "마곡 날씨", weather_text)
else:
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("👤 나 (User)")
        user_birth = st.date_input("내 생년월일", value=datetime.date(1990, 1, 1), key="u_birth")
        r1, r2 = st.columns(2)
        with r1: user_gender = st.radio("내 성별", ["남성", "여성"], key="u_gen")
        with r2: user_mbti = st.selectbox("내 MBTI", mbti_list, key="u_mbti")
    with col_right:
        label = "🏠 가족/애인" if "가족" in mode else "🤝 상사/동료"
        st.subheader(f"{label} (Target)")
        target_birth = st.date_input("상대 생년월일", value=datetime.date(1990, 1, 1), key="t_birth")
        r1, r2 = st.columns(2)
        with r1: target_gender = st.radio("상대 성별", ["남성", "여성"], key="t_gen")
        with r2: target_mbti = st.selectbox("상대 MBTI", ["모름"] + mbti_list, key="t_mbti")

    # 데이터 계산
    user_lunar = get_lunar_date(user_birth)
    user_zodiac = get_zodiac_sign(user_birth.day, user_birth.month)
    user_animal = get_korean_zodiac(user_birth)
    target_lunar = get_lunar_date(target_birth)
    target_zodiac = get_zodiac_sign(target_birth.day, target_birth.month)
    target_animal = get_korean_zodiac(target_birth)

    # 6개 카드 출력 (복구됨)
    cl, cr = st.columns(2)
    with cl:
        sc1, sc2, sc3 = st.columns(3)
        display_card(sc1, "⭐", "별자리", user_zodiac)
        display_card(sc2, "🐾", "띠", f"{user_animal}띠")
        display_card(sc3, "🌕", "음력", user_lunar)
    with cr:
        sc1, sc2, sc3 = st.columns(3)
        display_card(sc1, "⭐", "별자리", target_zodiac)
        display_card(sc2, "🐾", "띠", f"{target_animal}띠")
        display_card(sc3, "🌕", "음력", target_lunar)

st.write("")
st.markdown("---")

# --- 7. 전략 분석 로직 ---
btn_label = "🚀 전략 분석 시작"
if "가족" in mode: btn_label = "💕 평화/사랑 전략 수립"
elif "상사" in mode: btn_label = "🤝 사회생활 공략법 분석"

if st.button(btn_label, type="primary", use_container_width=True):
    st.session_state.lucky_item_revealed = False # 초기화
    with st.spinner("분석 엔진 가동 중..."):
        user_info = f"User: {user_mbti}, {user_zodiac}, {user_animal}띠"
        target_info = f"Target: {target_mbti}, {target_zodiac}, {target_animal}띠" if "나 혼자" not in mode else "N/A"
        
        prompt = f"""
        Analyze today's strategy. Mode: {mode}, Weather: {weather_text}
        {user_info} | {target_info}
        Format: KEY1|KEY2|KEY3|KEY4 (1st line)
        Then detailed markdown.
        """
        try:
            response = model.generate_content(prompt)
            full_text = response.text.strip()
            lines = full_text.split('\n')
            st.session_state.analysis_result = {
                "summary": lines[0].split('|'),
                "detail": "\n".join(lines[1:])
            }
            st.session_state.analysis_done = True
        except Exception as e:
            st.error(f"분석 마감 또는 오류: {e}")

# --- 8. 결과 디스플레이 및 행운템 뽑기 ---
if st.session_state.analysis_done:
    s = st.session_state.analysis_result["summary"]
    t1, t2, t3, t4 = "오늘의 총운", "관계 전략", "핵심 미션", "행운템"
    if "가족" in mode: t1, t2, t3, t4 = "애정/가정운", "상대 공략", "추천 활동", "치트키"
    elif "상사" in mode: t1, t2, t3, t4 = "의전 운세", "보고 타이밍", "점심 추천", "대화 주제"

    r1, r2, r3, r4 = st.columns(4)
    display_card(r1, "⚡", t1, s[0])
    display_card(r2, "🎯", t2, s[1])
    display_card(r3, "🔥", t3, s[2])
    
    # 4번째 카드를 행운템 뽑기 카드로 활용
    with r4:
        if st.session_state.lucky_item_revealed:
            display_card(r4, "🍀", t4, s[3])
        else:
            st.markdown(f'<div class="info-card"><div class="big-icon">🎁</div><div class="card-title">{t4}</div><div class="card-value">아래에서 확인!</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(st.session_state.analysis_result["detail"])

    # --- 행운템 뽑기 인터랙션 ---
    st.markdown("---")
    st.subheader(f"🎁 오늘의 {t4} 확인하기")
    col_anim, col_btn = st.columns([1, 2])
    
    with col_anim:
        if not st.session_state.lucky_item_revealed:
            lottie_box = load_lottieurl("https://lottie.host/170b6d21-f09d-473d-9861-f0f90e5414d7/oV2uQjQ2tM.json")
            if lottie_box: st_lottie(lottie_box, height=150, key="box_draw")
        else:
            st.markdown(f"<h1 style='text-align: center; font-size: 80px;'>🍀</h1>", unsafe_allow_html=True)

    with col_btn:
        if not st.session_state.lucky_item_revealed:
            if st.button("✨ 결과 열어보기", use_container_width=True):
                st.session_state.lucky_item_revealed = True
                st.balloons()
                st.rerun()
        else:
            st.success(f"오늘의 {t4}: **{s[3].strip()}**")
            st.info("이 결과는 당신의 데이터를 기반으로 추출된 맞춤형 행운입니다!")

    # 공유하기
    share_text = f"[오늘의 눈치 레이더]\n⚡ {t1}: {s[0]}\n🎯 {t2}: {s[1]}\n🔥 {s[2]}\n🍀 {t4}: {s[3]}\n\n👉 https://nunchi-radar.streamlit.app"
    st.code(share_text, language="text")
