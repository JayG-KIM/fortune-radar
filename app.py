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

# --- 2. AI 모델 설정 (Gemini 2.5 Flash) ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction="당신은 'AI 처세술 전략 엔진'입니다. 사용자와 상대방의 기질, 환경(날씨)을 분석하여 구체적인 행동 전략을 제시합니다."
    )
except Exception as e:
    st.error(f"System Error: {e}")

# --- 3. CSS 스타일 정의 ---
st.markdown("""
<style>
.info-card { background-color: #1E1E1E; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #333; margin-bottom: 5px; height: 110px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
.big-icon { font-size: 24px; margin-bottom: 5px; }
.card-title { font-size: 12px; font-weight: 600; color: #A0A0A0; margin-bottom: 2px; text-transform: uppercase; }
.card-value { font-size: 14px; color: #FFFFFF; font-weight: 500; word-break: keep-all; }
.title-container { text-align: left; margin-bottom: 10px; }
.main-title { font-size: 28px; font-weight: bold; color: #FFFFFF; margin-bottom: 5px; line-height: 1.2; }
.sub-title { font-size: 14px; color: #CCCCCC; margin-bottom: 5px; line-height: 1.5; }
.highlight { color: #00D4FF; font-weight: bold; }
.weather-badge { background-color: #333; color: #fff; padding: 5px 10px; border-radius: 15px; font-size: 12px; margin-left: 10px; vertical-align: middle; }
.engine-tag { display: inline-block; font-size: 11px; color: #00D4FF; border: 1px solid #00D4FF; padding: 4px 10px; border-radius: 15px; background-color: rgba(0, 212, 255, 0.05); margin-top: 5px; }
.quota-error { background-color: #2b1c1c; border: 1px solid #ff4b4b; color: #ffcccc; padding: 15px; border-radius: 8px; margin-top: 20px; font-size: 15px; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# --- 4. 데이터 매핑 및 함수 (원본 로직 복구) ---
ZODIAC_ICONS = {
    "염소자리": "🐐", "물병자리": "🏺", "물고기자리": "🐟", "양자리": "🐏",
    "황소자리": "🐂", "쌍둥이자리": "👯", "게자리": "🦀", "사자자리": "🦁",
    "처녀자리": "🧚", "천칭자리": "⚖️", "전갈자리": "🦂", "사수자리": "🏹"
}

ANIMAL_ICONS = {
    "쥐": "🐭", "소": "🐮", "호랑이": "🐯", "토끼": "🐰", "용": "🐲", "뱀": "🐍",
    "말": "🐴", "양": "🐑", "원숭이": "🐵", "닭": "🐔", "개": "🐶", "돼지": "🐷"
}

@st.cache_data(ttl=1800)
def get_real_kma_weather():
    nx, ny = 58, 126
    now = datetime.datetime.now()
    base_time_obj = now - datetime.timedelta(minutes=40)
    base_date = base_time_obj.strftime("%Y%m%d")
    base_time = base_time_obj.strftime("%H00")
    url = f"http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst?serviceKey={WEATHER_API_KEY}&pageNo=1&numOfRows=1000&dataType=JSON&base_date={base_date}&base_time={base_time}&nx={nx}&ny={ny}"
    try:
        response = requests.get(url, timeout=3)
        data = response.json()
        items = data['response']['body']['items']['item']
        weather_data = {item['category']: item['obsrValue'] for item in items}
        pty = int(weather_data.get('PTY', 0))
        temp = weather_data.get('T1H', '?')
        icon, status = "☀️", "맑음"
        if pty in [1, 5]: icon, status = "☔", "비"
        elif pty in [2, 6]: icon, status = "🌨️", "비/눈"
        elif pty in [3, 7]: icon, status = "☃️", "눈"
        return icon, f"{status} {temp}℃"
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

def get_ipchun_date(year):
    # 사용자가 작성한 입춘 로직 복구
    if year in [2021, 2025]: return datetime.date(year, 2, 3)
    if 1920 <= year <= 1984 and (year % 4 == 0): return datetime.date(year, 2, 5)
    return datetime.date(year, 2, 4)

def get_korean_zodiac(date_obj):
    year = date_obj.year
    ipchun = get_ipchun_date(year)
    target_year = year if date_obj >= ipchun else year - 1
    animals = ["원숭이", "닭", "개", "돼지", "쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양"]
    return animals[target_year % 12]

def display_card(column, icon, title, value):
    with column:
        st.markdown(f'<div class="info-card"><div class="big-icon">{icon}</div><div class="card-title">{title}</div><div class="card-value">{value}</div></div>', unsafe_allow_html=True)

def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- 5. 세션 상태 관리 ---
if 'analysis_done' not in st.session_state: st.session_state.analysis_done = False
if 'lucky_item_revealed' not in st.session_state: st.session_state.lucky_item_revealed = False
if 'analysis_result' not in st.session_state: st.session_state.analysis_result = {}

# --- 6. 사이드바 및 레이아웃 ---
with st.sidebar:
    st.header("😎 모드 선택")
    mode = st.radio("전략 모드", ["💼 나 혼자 (직장 생존)", "🏠 가족/애인 (평화 유지)", "🤝 상사/동료 (사회생활)"], index=0)
    st.markdown("---")
    st.caption("Ver 2.5.0 (Original Logic Restored)")

weather_icon, weather_text = get_real_kma_weather()

# 제목 및 서브타이틀
weather_html = f"<span class='weather-badge'>{weather_icon} 마곡 {weather_text}</span>"
if "나 혼자" in mode:
    subtitle_text = "데이터로 분석한 <span class='highlight'>오늘의 직장 생존 전략</span>"
    weather_html = "" # 나혼자 모드일 땐 원본처럼 뱃지 숨김 (카드에는 표시)
elif "가족" in mode:
    subtitle_text = "평화로운 관계를 위한 <span class='highlight'>로맨스/가족 전략</span>"
else:
    subtitle_text = "성공적인 사회생활을 위한 <span class='highlight'>관계 공략법</span>"

st.markdown(f'<div class="title-container"><span class="main-title">오늘의 눈치 레이더</span>{weather_html if "나 혼자" not in mode else ""}<div class="sub-title">{subtitle_text}</div><div class="engine-tag">Powered by AI Work Strategy Engine</div></div><hr style="border-top: 1px solid #333; margin-top: 5px; margin-bottom: 15px;">', unsafe_allow_html=True)

# --- 7. 입력 폼 (날짜 범위 1920~2026 복구) ---
mbti_list = ["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"]
today = datetime.date(2026, 2, 20)

if "나 혼자" in mode:
    st.subheader("👤 내 정보")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: user_birth = st.date_input("내 생년월일", value=datetime.date(1990, 1, 1), min_value=datetime.date(1920, 1, 1), max_value=today)
    with c2: user_gender = st.radio("내 성별", ["남성", "여성"], horizontal=True)
    with c3: user_mbti = st.selectbox("내 MBTI", mbti_list)
    
    user_lunar = get_lunar_date(user_birth)
    user_zodiac = get_zodiac_sign(user_birth.day, user_birth.month)
    user_animal = get_korean_zodiac(user_birth)
    
    c1, c2, c3, c4 = st.columns(4)
    display_card(c1, ZODIAC_ICONS.get(user_zodiac, "⭐"), "내 별자리", user_zodiac)
    display_card(c2, ANIMAL_ICONS.get(user_animal, "🐾"), "내 띠", f"{user_animal}띠")
    display_card(c3, "🌕", "음력 생일", user_lunar)
    display_card(c4, weather_icon, "마곡 날씨", weather_text)
else:
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("👤 나 (User)")
        user_birth = st.date_input("내 생년월일", value=datetime.date(1990, 1, 1), min_value=datetime.date(1920, 1, 1), max_value=today, key="u_b")
        r1, r2 = st.columns(2)
        with r1: user_gender = st.radio("내 성별", ["남성", "여성"], key="u_g")
        with r2: user_mbti = st.selectbox("내 MBTI", mbti_list, key="u_m")
    with col_right:
        label = "🏠 가족/애인" if "가족" in mode else "🤝 상사/동료"
        st.subheader(f"{label} (Target)")
        target_birth = st.date_input("상대 생년월일", value=datetime.date(1990, 1, 1), min_value=datetime.date(1920, 1, 1), max_value=today, key="t_b")
        r1, r2 = st.columns(2)
        with r1: target_gender = st.radio("상대 성별", ["남성", "여성"], key="t_g")
        with r2: target_mbti = st.selectbox("상대 MBTI", ["모름/선택안함"] + mbti_list, key="t_m")

    user_lunar, user_zodiac, user_animal = get_lunar_date(user_birth), get_zodiac_sign(user_birth.day, user_birth.month), get_korean_zodiac(user_birth)
    target_lunar, target_zodiac, target_animal = get_lunar_date(target_birth), get_zodiac_sign(target_birth.day, target_birth.month), get_korean_zodiac(target_birth)

    cl, cr = st.columns(2)
    with cl:
        sc1, sc2, sc3 = st.columns(3)
        display_card(sc1, ZODIAC_ICONS.get(user_zodiac, "⭐"), "별자리", user_zodiac)
        display_card(sc2, ANIMAL_ICONS.get(user_animal, "🐾"), "띠", f"{user_animal}띠")
        display_card(sc3, "🌕", "음력", user_lunar)
    with cr:
        sc1, sc2, sc3 = st.columns(3)
        display_card(sc1, ZODIAC_ICONS.get(target_zodiac, "⭐"), "별자리", target_zodiac)
        display_card(sc2, ANIMAL_ICONS.get(target_animal, "🐾"), "띠", f"{target_animal}띠")
        display_card(sc3, "🌕", "음력", target_lunar)

st.write("")
st.markdown("---")

# --- 8. 분석 로직 ---
btn_label = "🚀 전략 분석 시작"
if "가족" in mode: btn_label = "💕 평화/사랑 전략 수립"
elif "상사" in mode: btn_label = "🤝 사회생활 공략법 분석"

if st.button(btn_label, type="primary", use_container_width=True):
    st.session_state.lucky_item_revealed = False
    st.session_state.lucky_item = None # 행운템 초기화
    with st.spinner("AI 분석 중..."):
        try:
            target_str = f"Target: {target_mbti}, {target_zodiac}, {target_animal}" if "나 혼자" not in mode else "Solo"
            # 행운템을 제외한 3가지 핵심 키워드만 요청 (KEY4 삭제)
            prompt = f"Date: {today}, Weather: {weather_text}. Mode: {mode}. User: {user_mbti}, {user_zodiac}, {user_animal}. {target_str}. Format: KEY1|KEY2|KEY3 then detail."
            response = model.generate_content(prompt)
            full_text = response.text.strip()
            lines = full_text.split('\n')
            st.session_state.analysis_result = {"summary": lines[0].split('|'), "detail": "\n".join(lines[1:])}
            st.session_state.analysis_done = True
        except Exception as e: st.error(f"분석 실패: {e}")

# --- 9. 결과 및 행운템 뽑기 ---
if st.session_state.analysis_done:
    s = st.session_state.analysis_result["summary"]
    t1, t2, t3, t4 = "오늘의 총운", "관계 전략", "핵심 미션", "행운템"
    if "가족" in mode: t1, t2, t3, t4 = "애정/가정운", "상대 공략", "추천 활동", "치트키"
    elif "상사" in mode: t1, t2, t3, t4 = "의전 운세", "보고 타이밍", "점심 추천", "대화 주제"

    r1, r2, r3, r4 = st.columns(4)
    display_card(r1, "⚡", t1, s[0] if len(s) > 0 else "분석중")
    display_card(r2, "🎯", t2, s[1] if len(s) > 1 else "분석중")
    display_card(r3, "🔥", t3, s[2] if len(s) > 2 else "분석중")
    
    # 4번째 카드는 버튼 클릭 전까지 '미확인'으로 표시
    with r4:
        if st.session_state.lucky_item_revealed and 'lucky_item' in st.session_state:
            display_card(r4, "🍀", t4, st.session_state.lucky_item)
        else:
            st.markdown(f'<div class="info-card"><div class="big-icon">🎁</div><div class="card-title">{t4}</div><div class="card-value">아래 버튼 클릭!</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(st.session_state.analysis_result["detail"])
    
    st.markdown("---")
    st.subheader(f"🎁 오늘의 {t4} 뽑기")
    ca, cb = st.columns([1, 2])
    with ca:
        if not st.session_state.lucky_item_revealed:
            lottie_box = load_lottieurl("https://lottie.host/170b6d21-f09d-473d-9861-f0f90e5414d7/oV2uQjQ2tM.json")
            if lottie_box: st_lottie(lottie_box, height=150, key="box")
        else:
            st.markdown("<h1 style='text-align: center; font-size: 80px;'>🍀</h1>", unsafe_allow_html=True)
            
    with cb:
        if not st.session_state.lucky_item_revealed:
            st.write(f"상단의 분석 내용과는 별개로, 오늘 당신에게 필요한 **'실물 행운 아이템'**을 AI가 새롭게 추천합니다.")
            if st.button("✨ 결과 확인하기", use_container_width=True):
                # 구체적인 물건을 뽑아내기 위한 전용 프롬프트
                lucky_prompt = f"사용자 정보({user_mbti}, {user_zodiac})와 오늘 날씨({weather_text})를 고려해서, 오늘 가방에 넣거나 먹으면 운이 좋아질 '구체적인 실물 물건' 하나만 추천해줘. (예: 노란 포스트잇, 초코에몽, 죽부인, 빨간 볼펜 등). 수식어 빼고 '물건 이름'만 딱 한 줄로 말해."
                try:
                    res = model.generate_content(lucky_prompt)
                    st.session_state.lucky_item = res.text.strip()
                    st.session_state.lucky_item_revealed = True
                    st.balloons()
                    st.rerun()
                except:
                    st.session_state.lucky_item = "따뜻한 아메리카노"
                    st.session_state.lucky_item_revealed = True
                    st.rerun()
        else:
            st.info(f"오늘 당신을 지켜줄 {t4}: **{st.session_state.lucky_item}**")
            share_txt = f"[오늘의 눈치 레이더]\n⚡ {t1}: {s[0]}\n🎯 {t2}: {s[1]}\n🍀 {t4}: {st.session_state.lucky_item}\n👉 https://nunchi-radar.streamlit.app"
            st.code(share_txt, language="text")
