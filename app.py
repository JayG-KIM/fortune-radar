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

# 디버그 모드 확인
DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"

st.set_page_config(
    page_title="오늘의 눈치 레이더",
    page_icon="📡",
    layout="wide"
)

# CSS: 스타일 정의
st.markdown("""
<style>
    .info-card {
        background-color: #1E1E1E;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #333;
        margin-bottom: 5px;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .big-icon { font-size: 24px; margin-bottom: 5px; }
    .card-title {
        font-size: 12px;
        font-weight: 600;
        color: #A0A0A0;
        margin-bottom: 2px;
        text-transform: uppercase;
    }
    .card-value {
        font-size: 14px;
        color: #FFFFFF;
        font-weight: 500;
        word-break: keep-all;
    }
    .title-container {
        text-align: left;
        margin-bottom: 10px;
    }
    .main-title { 
        font-size: 28px; 
        font-weight: bold; 
        color: #FFFFFF; 
        margin-bottom: 5px;
        line-height: 1.2;
    }
    .sub-title { 
        font-size: 14px; 
        color: #CCCCCC; 
        margin-bottom: 5px; 
        line-height: 1.5;
    }
    .highlight { color: #00D4FF; font-weight: bold; }
    
    .weather-badge {
        background-color: #333;
        color: #fff;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 12px;
        margin-left: 10px;
        vertical-align: middle;
    }
    
    .engine-tag { 
        display: inline-block;
        font-size: 11px; 
        color: #00D4FF; 
        border: 1px solid #00D4FF; 
        padding: 4px 10px; 
        border-radius: 15px; 
        background-color: rgba(0, 212, 255, 0.05);
        margin-top: 5px;
    }

    .quota-error {
        background-color: #2b1c1c;
        border: 1px solid #ff4b4b;
        color: #ffcccc;
        padding: 15px;
        border-radius: 8px;
        margin-top: 20px;
        font-size: 15px;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. AI 모델 설정 ---
SYSTEM_PROMPT = """
당신은 'AI 처세술 전략 엔진'입니다. 
사용자와 상대방의 기질, 환경(날씨)을 분석하여 구체적인 행동 전략을 제시합니다.
"""

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name='gemini-2.0-flash', # 모델명은 현재 가용 버전에 맞게 수정 가능
        system_instruction=SYSTEM_PROMPT
    )
except Exception as e:
    st.error(f"System Error: {e}")

# --- 3. 데이터 매핑 및 보조 함수 ---
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
    
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    params = {
        "serviceKey": WEATHER_API_KEY, "pageNo": "1", "numOfRows": "1000", 
        "dataType": "JSON", "base_date": base_date, "base_time": base_time, 
        "nx": nx, "ny": ny
    }
    try:
        response = requests.get(url, params=params, timeout=3)
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
    except:
        return "📡 수신불가", "데이터 없음"

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

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
    year = date_obj.year
    animals = ["원숭이", "닭", "개", "돼지", "쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양"]
    return animals[year % 12]

def display_card(column, icon, title, value):
    with column:
        st.markdown(f"""
        <div class="info-card">
            <div class="big-icon">{icon}</div>
            <div class="card-title">{title}</div>
            <div class="card-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

# 행운템 생성 함수 (다양성 강화 버전)
def generate_lucky_item(mode, weather_text, user_info):
    prompt = f"""
    당신은 엉뚱하고 재미있는 행운 아이템 추천 전문가입니다.
    [상황] 모드: {mode}, 현재날씨: {weather_text}, 사용자 정보: {user_info}
    
    [가이드라인]
    1. 날씨에만 국한되지 마세요. (따뜻한 음료 같은 뻔한 건 금지)
    2. 아이템 카테고리를 섞으세요: 사무실 용품, 레트로 아이템, 먹거리, 엉뚱한 물건.
    3. 예시: 죽부인, 빨간 볼펜, 90년대 껌, 노란색 양말, 돌하르방 피규어, 유선 헤드셋 등.
    4. 반드시 '아이템 이름'만 딱 한 줄로 출력하세요. 설명은 생략합니다.
    """
    try:
        if DEBUG_MODE: return "죽부인"
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "행운의 네잎클로버"

# --- 4. 메인 UI 및 세션 상태 ---
if 'analysis_done' not in st.session_state: st.session_state.analysis_done = False
if 'lucky_item' not in st.session_state: st.session_state.lucky_item = None
if 'analysis_result' not in st.session_state: st.session_state.analysis_result = {}

with st.sidebar:
    st.header("😎 모드 선택")
    mode = st.radio("전략 모드", ["💼 나 혼자 (직장 생존)", "🏠 가족/애인 (평화 유지)", "🤝 상사/동료 (사회생활)"], index=0)
    st.markdown("---")
    st.caption(f"Ver 2.5.0 (Interaction Pack)")

weather_icon, weather_text = get_real_kma_weather()
subtitle_text = "데이터로 분석한 <span class='highlight'>오늘의 직장 생존 전략</span>"
weather_html = f"<span class='weather-badge'>{weather_icon} 마곡 {weather_text}</span>"

st.markdown(f"""
<div class="title-container">
    <span class="main-title">오늘의 눈치 레이더</span>{weather_html}
    <div class="sub-title">{subtitle_text}</div>
    <div class="engine-tag">Powered by AI Work Strategy Engine</div>
</div>
<hr style="border-top: 1px solid #333; margin-top: 5px; margin-bottom: 15px;">
""", unsafe_allow_html=True)

mbti_list = ["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"]

if "나 혼자" in mode:
    st.subheader("👤 내 정보")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: user_birth = st.date_input("내 생년월일", value=datetime.date(1990, 1, 1), min_value=datetime.date(1920, 1, 1))
    with c2: user_gender = st.radio("내 성별", ["남성", "여성"], horizontal=True)
    with c3: user_mbti = st.selectbox("내 MBTI", mbti_list)
else:
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("👤 나 (User)")
        user_birth = st.date_input("내 생년월일", value=datetime.date(1990, 1, 1), min_value=datetime.date(1920, 1, 1))
        r1, r2 = st.columns(2)
        with r1: user_gender = st.radio("내 성별", ["남성", "여성"], horizontal=True)
        with r2: user_mbti = st.selectbox("내 MBTI", mbti_list)
    with col_right:
        label = "🏠 가족/애인" if "가족" in mode else "🤝 상사/동료"
        st.subheader(f"{label} (Target)")
        target_birth = st.date_input("상대 생년월일", value=datetime.date(1990, 1, 1), min_value=datetime.date(1920, 1, 1))
        r1, r2 = st.columns(2)
        with r1: target_gender = st.radio("상대 성별", ["남성", "여성"], horizontal=True)
        with r2: target_mbti = st.selectbox("상대 MBTI", ["모름/선택안함"] + mbti_list)

user_lunar = get_lunar_date(user_birth)
user_zodiac_name = get_zodiac_sign(user_birth.day, user_birth.month)
user_animal_name = get_korean_zodiac(user_birth)
user_z_icon = ZODIAC_ICONS.get(user_zodiac_name, "⭐")
user_a_icon = ANIMAL_ICONS.get(user_animal_name, "🐾")

# 상단 카드 디스플레이
c1, c2, c3, c4 = st.columns(4)
display_card(c1, user_z_icon, "내 별자리", user_zodiac_name)
display_card(c2, user_a_icon, "내 띠", f"{user_animal_name}띠")
display_card(c3, "🌕", "음력 생일", user_lunar)
display_card(c4, weather_icon, "마곡 날씨", weather_text)

st.write("")
btn_label = "🚀 전략 분석 시작"
if st.button(btn_label, type="primary", use_container_width=True):
    st.session_state.lucky_item = None # 초기화
    with st.spinner("사무실 공기 분석 중..."):
        user_info_str = f"MBTI: {user_mbti}, 별자리: {user_zodiac_name}, 띠: {user_animal_name}"
        prompt = f"""
        [상황] {mode}, 날씨: {weather_text}, 유저: {user_info_str}
        위 정보를 바탕으로 오늘 하루 전략을 세워주세요.
        첫 줄은 '총운|관계전략|미션|행운힌트' 형식으로 작성하고, 
        그 아래 상세 내용을 마크다운으로 작성하세요.
        """
        try:
            if DEBUG_MODE:
                full_text = "최고의 날|적극적 대화|보고서 마무리|준비된 행운\n\n### 상세분석\n오늘 운이 아주 좋습니다!"
            else:
                response = model.generate_content(prompt)
                full_text = response.text.strip()
            
            lines = full_text.split('\n')
            st.session_state.analysis_result = {
                "summary": lines[0].split('|'),
                "detail": "\n".join(lines[1:])
            }
            st.session_state.analysis_done = True
        except:
            st.error("분석 실패. 다시 시도해 주세요.")

# --- 5. 결과 및 행운템 뽑기 애니메이션 ---
if st.session_state.analysis_done:
    res = st.session_state.analysis_result
    s = res["summary"]
    
    r1, r2, r3, r4 = st.columns(4)
    display_card(r1, "⚡", "오늘의 총운", s[0])
    display_card(r2, "🎯", "관계 전략", s[1])
    display_card(r3, "🔥", "핵심 미션", s[2])
    
    # 4번째 카드는 행운템 뽑기 유도
    with r4:
        if st.session_state.lucky_item:
            display_card(r4, "🍀", "행운 아이템", st.session_state.lucky_item)
        else:
            st.markdown(f"""<div class="info-card"><div class="big-icon">🎁</div><div class="card-title">럭키 박스</div><div class="card-value">아래 버튼 클릭!</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(res["detail"])
    
    # 행운템 뽑기 구역
    st.subheader("📋 오늘의 리미티드 행운템")
    col_draw, col_info = st.columns([1, 2])
    
    with col_draw:
        if not st.session_state.lucky_item:
            # 뽑기 상자 Lottie (무료 리소스)
            lottie_box = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_8u9v60.json")
            if lottie_box: st_lottie(lottie_box, height=150, key="box")
            if st.button("🎁 행운템 뽑기!", use_container_width=True):
                with st.spinner("행운 데이터 추출 중..."):
                    time.sleep(1) # 애니메이션 느낌
                    st.session_state.lucky_item = generate_lucky_item(mode, weather_text, user_info_str)
                    st.rerun()
        else:
            st.markdown(f"<h1 style='text-align: center;'>{st.session_state.lucky_item}</h1>", unsafe_allow_html=True)
            st.balloons()

    with col_info:
        if st.session_state.lucky_item:
            st.info(f"선택된 행운템: **{st.session_state.lucky_item}**")
            st.write("이 아이템을 소지하거나 떠올리는 것만으로도 오늘 업무의 긴장도가 15% 감소합니다. (AI 시뮬레이션 결과)")
        else:
            st.write("상자를 클릭하여 오늘 나에게 필요한 엉뚱한 행운템을 확인하세요!")

    # 공유하기
    st.markdown("---")
    share_text = f"[오늘의 눈치 레이더]\n\n⚡ {s[0]}\n🎯 {s[1]}\n🔥 {s[2]}\n🍀 행운템: {st.session_state.lucky_item or '뽑기 대기 중'}\n\n👉 확인하기: https://nunchi-radar.streamlit.app"
    st.code(share_text, language="text")
    st.caption("복사해서 동료나 가족에게 공유해 보세요!")
