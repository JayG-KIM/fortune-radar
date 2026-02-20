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

# 디버그 모드 확인 (환경변수가 'True'일 때만 작동)
DEBUG_MODE = os.getenv("DEBUG_MODE", "False") == "True"

st.set_page_config(
    page_title="오늘의 눈치 레이더",
    page_icon="📡",
    layout="wide"
)

# CSS: 모던하고 전략적인 디자인
st.markdown("""
<style>
    .info-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #333;
        margin-bottom: 10px;
        height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .big-icon { font-size: 32px; margin-bottom: 8px; }
    .card-title {
        font-size: 14px;
        font-weight: 600;
        color: #A0A0A0;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .card-value {
        font-size: 16px;
        color: #FFFFFF;
        font-weight: 500;
        word-break: keep-all;
    }
    .title-container {
        text-align: left;
        margin-bottom: 20px;
    }
    .main-title { 
        font-size: 32px; 
        font-weight: bold; 
        color: #FFFFFF; 
        margin-bottom: 5px;
        line-height: 1.2;
    }
    .sub-title { 
        font-size: 16px; 
        color: #CCCCCC; 
        margin-bottom: 10px; 
        line-height: 1.5;
    }
    .highlight {
        color: #00D4FF;
        font-weight: bold;
    }
    .engine-tag { 
        display: inline-block;
        font-size: 11px; 
        color: #00D4FF; 
        border: 1px solid #00D4FF; 
        padding: 4px 10px; 
        border-radius: 15px; 
        background-color: rgba(0, 212, 255, 0.05);
    }
    /* 선착순 마감 에러 메시지 스타일 */
    .quota-error {
        background-color: #2b1c1c;
        border: 1px solid #ff4b4b;
        color: #ffcccc;
        padding: 15px;
        border-radius: 8px;
        margin-top: 20px;
        font-size: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. AI 모델 설정 ---
SYSTEM_PROMPT = """
당신은 '직장인 처세술 전략 엔진(AI Work Strategy Engine)'입니다.
미신적인 점집이 아니라, 사용자의 기질과 환경 변수(날씨, 시간)를 분석하여
가장 현실적이고 전략적인 직장 생활 가이드를 제공합니다.

[Tone & Manner]
1. 정중하지만 통찰력 있는 '전문 컨설턴트'의 어조를 유지하세요.
2. 반말이나 '김대리' 같은 특정 호칭은 절대 사용하지 마세요.
3. 추상적인 조언보다는 "오후 2시에 보고하세요", "따뜻한 국물을 드세요" 같이 구체적인 행동을 지시하세요.
"""

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=SYSTEM_PROMPT
    )
except Exception as e:
    st.error(f"System Error: {e}")

# --- 3. 데이터 매핑 및 함수 ---
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
        
        return icon, f"{status} ({temp}℃)"
    except:
        return "📡", "수신불가"

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

def get_korean_zodiac(year):
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

# --- 4. 메인 UI ---
st.markdown("""
    <div class="title-container">
        <div class="main-title">오늘의 눈치 레이더</div>
        <div class="sub-title">데이터로 분석한 <span class="highlight">오늘의 직장 생존 전략</span></div>
        <div class="engine-tag">Powered by AI Work Strategy Engine</div>
    </div>
    <hr style="border-top: 1px solid #333; margin-top: 10px;">
""", unsafe_allow_html=True)

if DEBUG_MODE:
    st.caption("🛠️ 현재 [개발자 테스트 모드]가 켜져 있습니다. API가 차감되지 않습니다.")

c_input1, c_input2, c_input3 = st.columns([2, 1, 1])
with c_input1:
    birth_date = st.date_input("📅 생년월일", value=datetime.date(2024, 3, 5), min_value=datetime.date(1920, 1, 1))
with c_input2:
    gender = st.radio("성별", ["남성", "여성"], horizontal=True)
with c_input3:
    mbti_list = ["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"]
    my_mbti = st.selectbox("MBTI (필수)", mbti_list)

lunar_date = get_lunar_date(birth_date)
zodiac_name = get_zodiac_sign(birth_date.day, birth_date.month)
animal_name = get_korean_zodiac(birth_date.year)
weather_icon, weather_text = get_real_kma_weather()

z_icon = ZODIAC_ICONS.get(zodiac_name, "⭐")
a_icon = ANIMAL_ICONS.get(animal_name, "🐾")

c1, c2, c3, c4 = st.columns(4)
display_card(c1, z_icon, "별자리", zodiac_name)
display_card(c2, a_icon, "띠", f"{animal_name}띠")
display_card(c3, "🌕", "음력 생일", lunar_date)
display_card(c4, weather_icon, "마곡 날씨", weather_text)

st.write("")
st.markdown("---")

# --- 5. 전략 분석 로직 ---
if st.button("🚀 전략 분석 시작", type="primary", use_container_width=True):
    
    loading_texts = [
        "📡 사무실의 공기를 읽는 중...",
        "📉 보이지 않는 역학 관계 계산 중...",
        "☁️ 마곡동 기상 변수 대입 중...",
        "🧠 최적의 보고 타이밍 계산 중..."
    ]
    
    with st.spinner(random.choice(loading_texts)):
        
        # [수정] 행운템 다양성과 의외성을 위한 프롬프트 가이드 보강
        strategy_prompt = f"""
        Analyze today's workplace strategy for the user.
        
        [Input Data]
        - Date: {datetime.date.today()}
        - Weather: {weather_text} (Affects mood/commute)
        - User: {animal_name} (Zodiac), {zodiac_name} (StarSign), {my_mbti} (MBTI)
        
        [Output Request]
        Generate a strategic briefing in Korean.
        IMPORTANT: The very first line MUST be the 4 summary keywords separated by '|'.
        
        [Guidelines for KEYWORD4 - Lucky Item (행운템)]
        1. Avoid repetitive or common items like 'warm coffee', 'herb tea', or 'hot water'.
        2. Provide a variety of specific items across different categories:
           - Tech: Noise-canceling headphones, a specific color of mouse, etc.
           - Office: High-quality fountain pen, a specific book title, vintage stapler, etc.
           - Comfort: Hand warmer, ergonomic cushion, blue light glasses, etc.
           - Unexpected/Quirky: Bamboo wife (죽부인), a specific color of socks, a nostalgic toy, a single rose, etc.
        3. Make the item feel personal and surprising, not just weather-dependent.

        Format:
        KEYWORD1|KEYWORD2|KEYWORD3|KEYWORD4
        ...
        """
        
        try:
            if DEBUG_MODE:
                time.sleep(1.5)
                full_text = """테스트 모드|API 미사용|무제한 테스트|죽부인
                
                ### 🛠️ 개발자 테스트 모드 브리핑
                현재 **DEBUG_MODE=True** 상태입니다.
                
                - **⚡ 오늘의 총운**: 이것은 테스트용 더미 텍스트입니다.
                - **🤝 상사/동료 전략**: 디버그 모드에서는 모든 동료가 친절합니다.
                - **📈 업무 및 성과**: 버그 없는 완벽한 하루가 예상됩니다.
                - **🛡️ 주의사항**: 배포 시에는 .env에서 DEBUG_MODE를 끄세요.
                - **🍀 행운의 요소**: 의외의 즐거움을 주는 **죽부인**을 곁에 두세요.
                """
            else:
                response = model.generate_content(strategy_prompt)
                full_text = response.text.strip()
            
            lines = full_text.split('\n')
            summary_line = None
            detail_lines = []
            
            found_summary = False
            for i, line in enumerate(lines):
                if "|" in line and not found_summary:
                    summary_line = line
                    found_summary = True
                else:
                    detail_lines.append(line)
            
            detail_text = "\n".join(detail_lines).strip()

            if summary_line:
                parts = summary_line.split('|')
            else:
                parts = ["분석 완료", "전략 수립", "기회 포착", "행운 가득"]

            while len(parts) < 4: parts.append("-")

            st.success("✅ 전략 브리핑이 생성되었습니다.")
            
            r1, r2, r3, r4 = st.columns(4)
            display_card(r1, "⚡", "오늘의 총운", parts[0].strip())
            display_card(r2, "🤝", "상사/동료", parts[1].strip())
            display_card(r3, "📈", "업무/성과", parts[2].strip())
            display_card(r4, "🍀", "행운템", parts[3].strip())
            
            st.markdown("---")
            st.markdown(detail_text)
            
        except Exception as e:
            error_msg = str(e)
            st.markdown(f"""
            <div class="quota-error">
                <strong>📢 아쉽네요! 오늘의 선착순 분석이 마감되었습니다.</strong><br><br>
                본 서비스는 하루 <strong>선착순 20명</strong>에게만 무료로 제공하고 있어요.<br>
                내일 아침에 다시 도전해보세요! (매일 자정 초기화)
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("개발자용 에러 상세 확인 (PO Only)"):
                st.error(f"실제 에러 내용: {error_msg}")
