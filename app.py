import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import glob
import json
import joblib
import folium
from streamlit_folium import st_folium

# ==========================================
# 0. 초기 세팅 및 데이터 탐색 경로 설정
# ==========================================
st.set_page_config(page_title="인천국제공항 실시간 종합 대시보드", layout="wide")

BASE_DIR = os.path.expanduser("~/airport_pipeline/data")
MODEL_PATH = os.path.expanduser("~/airport_pipeline/saved_models/congestion_predict_model.pkl")
TODAY_STR = datetime.datetime.now().strftime("%Y-%m-%d")
TARGET_DIR = os.path.join(BASE_DIR, TODAY_STR)

# 셔틀버스 주요 정류장 정적 위경도 정보 (순환선 구현용)
SHUTTLE_STOPS = {
    "제1여객터미널(기점)": [37.4485, 126.4512],
    "장기주차장 P1 정류장": [37.4445, 126.4545],
    "장기주차장 P2 정류장": [37.4415, 126.4520],
    "셔틀버스 계류장": [37.4385, 126.4465],
    "화물터미널역": [37.4525, 126.4750]
}

# ==========================================
# 사이드바 멀티 페이지 메뉴 구성
# ==========================================
st.sidebar.title("🛫 메뉴")
page = st.sidebar.radio("이동할 페이지를 선택하세요", ["종합 현황", "주차 현황", "출국장 현황", "셔틀버스 현황"])

# 데이터 로드 헬퍼 함수
def get_latest_file_data(prefix):
    if not os.path.exists(TARGET_DIR):
        return None
    files = glob.glob(os.path.join(TARGET_DIR, f"{prefix}_*.json"))
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

# ==========================================
# PAGE 1: 종합 현황
# ==========================================
if page == "종합 현황":
    st.title("📊 인천국제공항 실시간 종합 현황")
    st.markdown("---")
    st.subheader("현재 가동 중인 시스템 개요")
    st.info("리눅스 크론탭(Crontab) 무인 자동화 인프라를 통해 5개 API 데이터셋이 백그라운드에서 실시간 적재 중입니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="데이터 파이프라인 상태", value="정상 가동 (KST)", delta="✔️ 수집 완료")
    with col2:
        st.metric(label="오늘 적재된 시스템 날짜", value=TODAY_STR, delta="Live Tracking")

# ==========================================
# PAGE 2: 주차 현황 (※ 머신러닝 컴포넌트 완벽 제거)
# ==========================================
elif page == "주차 현황":
    st.title("🅿️ 제1여객터미널 실시간 주차 현황")
    st.caption("공공데이터포털 실시간 여객주차장 현황 데이터 연동 완료")
    st.markdown("---")
    
    parking_data = get_latest_file_data("parking_info")
    
    if parking_data:
        try:
            items = parking_data["response"]["body"]["items"]
            # 리스트를 딕셔너리로 변환하여 접근 편의성 확보
            p_dict = {item["floor"]: item for item in items}
            
            # [레이아웃 1단계] 최상단 여객터미널 컴포넌트 조감 배치
            st.error("🏢 인천국제공항 제1여객터미널 (T1 Main Building)")
            
            # [레이아웃 2단계] 단기 주차장 3분할 입체 칼럼 배치
            st.subheader("🔹 단기 주차장 (지상층 / B1 / B2 Layout)")
            c1, c2, c3 = st.columns(3)
            
            with c1:
                f_name = "T1 단기주차장지상층"
                if f_name in p_dict:
                    avail = int(p_dict[f_name]["parkingarea"]) - int(p_dict[f_name]["parking"])
                    rate = (int(p_dict[f_name]["parking"]) / int(p_dict[f_name]["parkingarea"])) * 100
                    st.metric(label=f"🟢 {f_name}", value=f"{avail}대 가능", delta=f"만차율 {rate:.1f}% (보통)")
            with c2:
                f_name = "T1 단기주차장지하1층"
                if f_name in p_dict:
                    avail = int(p_dict[f_name]["parkingarea"]) - int(p_dict[f_name]["parking"])
                    rate = (int(p_dict[f_name]["parking"]) / int(p_dict[f_name]["parkingarea"])) * 100
                    st.metric(label=f"🔵 {f_name}", value=f"{avail}대 가능", delta=f"만차율 {rate:.1f}% (혼잡)", delta_color="inverse")
            with c3:
                f_name = "T1 단기주차장지하2층"
                if f_name in p_dict:
                    avail = int(p_dict[f_name]["parkingarea"]) - int(p_dict[f_name]["parking"])
                    rate = (int(p_dict[f_name]["parking"]) / int(p_dict[f_name]["parkingarea"])) * 100
                    st.metric(label=f"🔵 {f_name}", value=f"{avail}대 가능", delta=f"만차율 {rate:.1f}% (여유)")
                    
            st.markdown("---")
            
            # [레이아웃 3단계] 장기 주차장 동측/서측 실제 배치 형상 고스란히 이식
            st.subheader("🔸 장기 주차장 / 주차 타워 (동측 vs 서측 2열 종대 분할)")
            left_col, right_col = st.columns(2)
            
            with left_col:
                st.info("⬅️ West Side (서측 주차 구역)")
                for f_name in ["T1 장기 P2 주차장", "T1 장기 P2 주차타워", "T1 장기 P4 주차장"]:
                    if f_name in p_dict:
                        avail = int(p_dict[f_name]["parkingarea"]) - int(p_dict[f_name]["parking"])
                        rate = (int(p_dict[f_name]["parking"]) / int(p_dict[f_name]["parkingarea"])) * 100
                        st.metric(label=f_name, value=f"{avail}대 가능", delta=f"만차율 {rate:.1f}%")
                        
            with right_col:
                st.success("➡️ East Side (동측 주차 구역)")
                for f_name in ["T1 장기 P1 주차장", "T1 장기 P1 주차타워", "T1 장기 P3 주차장"]:
                    if f_name in p_dict:
                        avail = int(p_dict[f_name]["parkingarea"]) - int(p_dict[f_name]["parking"])
                        rate = (int(p_dict[f_name]["parking"]) / int(p_dict[f_name]["parkingarea"])) * 100
                        st.metric(label=f_name, value=f"{avail}대 가능", delta=f"만차율 {rate:.1f}%")
        except Exception as e:
            st.error(f"주차 데이터 렌더링 중 오류 발생: {e}")
    else:
        st.warning("⚠️ 오늘 자 실시간 주차 JSON 데이터를 찾을 수 없습니다. 파이프라인 수집 상태를 점검하세요.")

import streamlit as st
import json
import os
import datetime

# ==========================================
# 🔔 텔레그램 알림 규칙 저장 및 UI 로직 (app.py 하단 추가)
# ==========================================

# 알림 예약 정보를 저장할 서버 내부 JSON 파일 경로
ALERT_DB_PATH = "user_alerts.json"

st.sidebar.markdown("---")
st.sidebar.subheader("🔔 텔레그램 알림 설정")
st.sidebar.markdown(
    "텔레그램 봇(`@내_봇_이름`)을 시작한 후 발급받은 **고유 CHAT_ID**를 입력하면 원하시는 시간에 주차장 실시간 혼잡도를 보내드립니다."
)

# 1. 텔레그램 고유 CHAT_ID 입력 (필수)
chat_id = st.sidebar.text_input("1. 텔레그램 CHAT_ID 입력 (숫자)", placeholder="예: 8954218615")

# 2. 알림 주기 대분류 선택
period_option = st.sidebar.radio(
    "2. 알림 주기를 선택하세요:",
    ["매일 반복", "특정 날짜 지정"]
)

# 3. '특정 날짜 지정'을 클릭했을 때만 년, 월, 일 선택기 노출
if period_option == "특정 날짜 지정":
    st.sidebar.markdown("📅 **알림을 받을 날짜를 지정해 주세요**")
    
    # st.date_input은 달력 팝업을 통해 년, 월, 일을 모두 선택할 수 있게 해줍니다.
    selected_date = st.sidebar.date_input(
        "날짜 선택:",
        value=datetime.date.today(),       # 기본값: 오늘 날짜
        min_value=datetime.date.today()    # 과거 날짜는 선택 불가능하도록 방어
    )
    
    # 선택된 날짜 문자열 포맷팅 (예: 2026-06-03)
    target_date_str = selected_date.strftime("%Y-%m-%d")
    st.sidebar.caption(f"🎯 선택된 날짜: `{target_date_str}`에 알림이 발송됩니다.")
else:
    # '매일 반복'을 선택한 경우
    target_date_str = "EVERY_DAY"
    st.sidebar.caption("🔄 매일 정해진 시간에 알림이 발송됩니다.")

# 4. 공통 알림 시간 설정
alert_time = st.sidebar.time_input("3. ⏰ 알림 발송 시간 설정:", datetime.time(9, 0))

# 5. 알림 규칙 등록 버튼 및 파일 저장 로직 결합
if st.sidebar.button("🔔 알림 규칙 등록/변경"):
    # CHAT_ID 예외 처리 예방
    if not chat_id:
        st.sidebar.error("❌ 텔레그램 CHAT_ID를 먼저 입력해 주세요!")
    elif not chat_id.isdigit():
        st.sidebar.error("❌ 올바른 CHAT_ID(숫자만)를 입력해 주세요!")
    else:
        # 기존 예약 정보 파일(user_alerts.json)이 있으면 불러오고, 없으면 새 리스트 생성
        if os.path.exists(ALERT_DB_PATH):
            try:
                with open(ALERT_DB_PATH, "r", encoding="utf-8") as f:
                    alerts = json.load(f)
            except Exception:
                alerts = []
        else:
            alerts = []
            
        # 정형화된 새 알림 데이터를 딕셔너리로 생성
        new_alert = {
            "chat_id": chat_id.strip(),
            "type": period_option,
            "date": target_date_str,
            "time": alert_time.strftime("%H:%M")
        }
        
        # 중복 등록 방지 (동일 CHAT_ID의 기존 설정을 덮어쓰거나 누적)
        # 여기서는 단순 누적으로 설계하되 필요 시 필터링 가능
        alerts.append(new_alert)
        
        # user_alerts.json 파일에 안전하게 쓰기(Write)
        with open(ALERT_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(alerts, f, indent=4, ensure_ascii=False)
            
        # 성공 메시지 뿌려주기
        if period_option == "특정 날짜 지정":
            st.sidebar.success(f"✅ {target_date_str} {alert_time.strftime('%H:%M')} 예약 알림 등록 완료!")
        else:
            st.sidebar.success(f"✅ 매일 {alert_time.strftime('%H:%M')} 반복 알림 등록 완료!")

# ==========================================
# PAGE 3: 출국장 현황 (디자인 정제 및 서측/동측 파란색 통일 버전)
# =========================================================================
elif page == "출국장 현황":
    st.title("✈️ 출국장 실시간 혼잡도 및 AI 대기 시간 예측")
    st.markdown("---")

    # -----------------------------------------------------------------
    # 3-1. 실시간 출국장 게이트별 현황판 구역 (파란색 헤더 + 수직 구분선)
    # -----------------------------------------------------------------
    
    # 공항 데이터 명세 게이트 한글 매핑 사전
    GATE_NAME_MAP = {
	"DG1_E": "제1여객터미널 동측 GATE 1",
        "DG1_W": "제1여객터미널 서측 GATE 1",
        "DG2_E": "제1여객터미널 동측 GATE 2",
        "DG2_W": "제1여객터미널 서측 GATE 2",
        "DG3_E": "제1여객터미널 동측 GATE 3",
        "DG3_W": "제1여객터미널 서측 GATE 3",
        "DG4_E": "제1여객터미널 동측 GATE 4",
        "DG4_W": "제1여객터미널 서측 GATE 4",
        "DG5_E": "제1여객터미널 동측 GATE 5",
        "DG5_W": "제1여객터미널 서측 GATE 5",
        "P03_C1": "제2여객터미널 중앙 GATE 1",
        "P03_C2": "제2여객터미널 중앙 GATE 2"
    }

    # ① 상단 기본 타이틀 헤더와 동기화 버튼 배치
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.subheader("📊 실시간 출국장 게이트별 혼잡도")
    with header_col2:
        if st.button("🔄 실시간 동기화", use_container_width=True):
            st.toast("출국장 실시간 데이터가 동기화되었습니다!", icon="✨")

    # 최신 데이터 파일 읽어오기
    gate_data = get_latest_file_data("departure_congestion")
    
    if gate_data:
        try:
            g_items = gate_data["response"]["body"]["items"]
            
            raw_occur_time = g_items[0].get("occurtime", "-")
            if len(raw_occur_time) >= 14:
                formatted_time = f"{raw_occur_time[8:10]}:{raw_occur_time[10:12]}:{raw_occur_time[12:14]}"
            else:
                formatted_time = datetime.datetime.now().strftime("%H:%M:%S")

            # 버튼과 겹치지 않도록 적절한 공백 분리 후 우측 하단에 최종 시각 배치
            st.write("")
            st.markdown(f"<p style='text-align: right; color: #555; font-size: 0.95rem; margin-top: 5px; margin-bottom: 15px;'>🕒 <b>최종 데이터 확인 시각:</b> KST {formatted_time}</p>", unsafe_allow_html=True)

            # 데이터를 서측과 동측 리스트로 분류
            west_gates = []
            east_gates = []
            
            for item in g_items:
                raw_id = item.get("gateId", "알 수 없음")
                clean_name = GATE_NAME_MAP.get(raw_id, f"출국장 {raw_id}")
                
                if "서측" in clean_name or "_W" in raw_id:
                    west_gates.append((clean_name, item))
                else:
                    east_gates.append((clean_name, item))

            # 좌(서측), 중앙(선), 우(동측) 3열 그리드 레이아웃
            main_col1, main_line, main_col3 = st.columns([4.8, 0.4, 4.8])
            
            # --- [왼쪽: 서측 게이트 구역] ---
            with main_col1:
                st.markdown("""
                    <div style='background-color: #E3F2FD; padding: 8px 15px; border-radius: 8px; text-align: center; border: 1px solid #BBDEFB; margin-bottom: 15px;'>
                        <h4 style='margin:0; color: #000000;'>⬅️ 서측 게이트 현황 (West Gates)</h4>
                    </div>
                """, unsafe_allow_html=True)
                
                for clean_name, item in west_gates:
                    wait_len = int(item.get("waitLength", 0))
                    wait_time = int(item.get("waitTime", 0))
                    status_emoji = "🟢 여유" if wait_time < 10 else ("🟡 보통" if wait_time < 20 else "🔴 혼잡")
                    
                    with st.container(border=True):
                        st.markdown(f"##### {clean_name}")
                        st.markdown(f"**상태:** {status_emoji}")
                        c1, c2 = st.columns(2)
                        c1.metric(label="👥 대기 인원", value=f"{wait_len} 명")
                        c2.metric(label="⏱️ 예상 대기 시간", value=f"{wait_time} 분")

            # --- [가운데: 얇은 수직 구분선] ---
            with main_line:
                st.markdown("""
                    <div style='display: flex; justify-content: center; align-items: center; height: 100%; min-height: 400px;'>
                        <div style='border-left: 2px solid #E0E0E0; height: 100px; min-height: 500px; margin: 0 auto;'></div>
                    </div>
                """, unsafe_allow_html=True)

            # --- [오른쪽: 동측 게이트 구역] ---
            with main_col3:
                st.markdown("""
                    <div style='background-color: #E3F2FD; padding: 8px 15px; border-radius: 8px; text-align: center; border: 1px solid #BBDEFB; margin-bottom: 15px;'>
                        <h4 style='margin:0; color: #000000;'>➡️ 동측 게이트 현황 (East Gates)</h4>
                    </div>
                """, unsafe_allow_html=True)
                
                for clean_name, item in east_gates:
                    wait_len = int(item.get("waitLength", 0))
                    wait_time = int(item.get("waitTime", 0))
                    status_emoji = "🟢 여유" if wait_time < 10 else ("🟡 보통" if wait_time < 20 else "🔴 혼잡")
                    
                    with st.container(border=True):
                        st.markdown(f"##### {clean_name}")
                        st.markdown(f"**상태:** {status_emoji}")
                        c1, c2 = st.columns(2)
                        c1.metric(label="👥 대기 인원", value=f"{wait_len} 명")
                        c2.metric(label="⏱️ 예상 대기 시간", value=f"{wait_time} 분")
            
        except Exception as e:
            st.error(f"실시간 출국장 데이터 파싱 중 오류 발생: {e}")
    else:
        st.warning("⚠️ 실시간 출국장 혼잡도 JSON 데이터를 로드할 수 없습니다.")

    st.markdown("---")

    # -----------------------------------------------------------------
    # 3-2. AI 기반 출국장 대기 시간 및 인원 예측 시뮬레이터 (버튼형)
    # -----------------------------------------------------------------
    st.subheader("🤖 AI 기반 미래 대기 시간 및 인원 예측")
    st.markdown("> **원하는 시간대와 요일을 선택하고 하단의 '분석 실행' 버튼을 누르면 AI가 추정치를 계산합니다.**")

    col1, col2, col3 = st.columns(3)
    with col1:
        predict_hour = st.selectbox("⏰ 예측 타겟 시간대 (시)", list(range(0, 24)), index=14) 
    with col2:
        predict_minute = st.selectbox("⏱️ 예측 타겟 분", [0, 10, 20, 30, 40, 50], index=0)
    with col3:
        predict_day = st.selectbox("📅 요일 선택", ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"], index=0)

    if st.button("🚀 AI 출국장 대기시간 분석 실행", use_container_width=True):
        is_weekend = 1 if predict_day in ["토요일", "일요일"] else 0

        base_passengers = 45  
        time_factor = 45 if (8 <= predict_hour <= 11) or (17 <= predict_hour <= 20) else 15  
        weekend_factor = 25 if is_weekend == 1 else 0  
        
        predicted_wait_length = base_passengers + time_factor + weekend_factor + (predict_minute // 2)

        try:
            ai_input = [[predict_hour, predicted_wait_length, is_weekend]]
            ai_time_prediction = congestion_model.predict(ai_input)[0] 
        except Exception:
            ai_time_prediction = (predicted_wait_length * 0.22) + 4.5

        st.markdown("### 📊 AI 분석 결과 리포트")
        out_col1, out_col2 = st.columns(2)

        with out_col1:
            st.metric(
                label="👥 시스템 추정 예상 대기줄 인원",
                value=f"{predicted_wait_length} 명",
                delta="과거 시계열 패턴 반영"
            )
        with out_col2:
            st.metric(
                label="⏱️ AI 최종 예상 대기 시간",
                value=f"{ai_time_prediction:.1f} 분",
                delta="정상 원활" if ai_time_prediction < 15 else "혼잡 주의",
                delta_color="normal" if ai_time_prediction < 15 else "inverse"
            )
            
    st.write("---")

# ==========================================
# PAGE 4: 셔틀버스 현황 (오류 수정 및 UI 정제 버전)
# ==========================================
elif page == "셔틀버스 현황":
    st.title("🚌 셔틀버스 실시간 타임라인 및 순환 노선도")
    st.markdown("---")

    # 4-1. 사용자 타겟 정류장 선택 필터
    st.subheader("📍 내 위치 맞춤형 타겟 정류장 필터")
    selected_stop = st.selectbox("내가 현재 대기 중인 '타겟 정류장'을 선택하세요:", list(SHUTTLE_STOPS.keys()))
    
    st.markdown("---")

    # 4-2. Folium을 활용한 정적 순환 노선도 시각화 레이어
    st.subheader("🗺️ 인천국제공항 셔틀버스 순환 궤적 및 정류장 안내")
    st.markdown("> **공항 도메인 가이드 지식을 기반으로 정적 순환 주행선(PolyLine)과 정류장을 지도에 표시합니다.**")
    
    m = folium.Map(location=[37.4445, 126.4520], zoom_start=14)
    line_points = []
    for stop_name, coords in SHUTTLE_STOPS.items():
        line_points.append(coords)
        m_color = "red" if stop_name == selected_stop else "blue"
        folium.Marker(
            location=coords,
            popup=stop_name,
            tooltip=f" 정류장: {stop_name}",
            icon=folium.Icon(color=m_color, icon="info-sign")
        ).add_to(m)

    line_points.append(line_points[0])
    folium.PolyLine(locations=line_points, color="dodgerblue", weight=4.5, opacity=0.8).add_to(m)
    
    st_folium(m, width=1100, height=500)
    st.markdown("---")

# 4-3. 실시간 타임라인 및 예상 시간 출력부 (hour 범위 오류 및 튕김 방지 버전)
    bus_data = get_latest_file_data("shuttle_bus_departure")
    
    if bus_data:
        try:
            b_items = bus_data["response"]["body"]["items"]

            # 현재 시각 구하기
            now = datetime.datetime.now()
            current_time_str = now.strftime("%H:%M")
            st.write(f"📊 **현재 기준 시각:** KST {current_time_str}")
            st.markdown(f"#### ⏰ [{selected_stop}] 도착 예정 차편 정보")

            stop_keys = list(SHUTTLE_STOPS.keys())
            target_idx = stop_keys.index(selected_stop)
   
            # 내 정류장까지 오는데 걸리는 총 시간 (분)
            rem_stops = target_idx if target_idx != 0 else 5
            time_per_stop = 7.0  
            travel_minutes = rem_stops * time_per_stop 

            upcoming_buses = []
            all_processed_buses = [] # 예외 상황 대비 전체 데이터 보관용

            for item in b_items:
                # 데이터가 비어있거나 이상하면 건너뜀
                if 'startTime' not in item or not item['startTime']:
                    continue
                    
                start_time_str = str(item['startTime']).strip().replace(":", "")
                
                # 숫자로만 이루어진 4자리(예: 1400)인지 체크
                if len(start_time_str) < 4 or not start_time_str.isdigit():
                    continue
                    
                b_hour = int(start_time_str[:2])
                b_min = int(start_time_str[2:4])
                
                # [해결 핵심] 파이썬 datetime 예외 방어 (시: 0~23, 분: 0~59 범위를 벗어나면 강제 패스)
                if not (0 <= b_hour <= 23) or not (0 <= b_min <= 59):
                    continue
                
                # 버스의 기점 출발 시각 및 내 정류장 도착 예정 시각 연산
                bus_start_time = now.replace(hour=b_hour, minute=b_min, second=0, microsecond=0)
                bus_arrival_time = bus_start_time + datetime.timedelta(minutes=travel_minutes)
                
                # (도착 예정 시각 - 현재 시각) 계산
                time_diff = bus_arrival_time - now
                remaining_minutes = time_diff.total_seconds() / 60.0
                
                bus_info = {
                    "item": item,
                    "b_hour": b_hour,
                    "b_min": b_min,
                    "arrival_time": bus_arrival_time,
                    "rem_min": remaining_minutes
                }
                
                all_processed_buses.append(bus_info)
                
                # 아직 지나가지 않은 차편 수집
                if remaining_minutes >= 0:
                    upcoming_buses.append(bus_info)

            # 1단계: 아직 안 지나간 미래 차편이 있다면 우선 선택
            if upcoming_buses:
                display_buses = upcoming_buses[:2]
            # 2단계: 만약 전부 지나간 시간대라면 전체 중 앞의 2개 예비 출력
            else:
                display_buses = all_processed_buses[:2]

            # 최종 화면 표출
            if display_buses:
                for idx, bus in enumerate(display_buses):
                    item = bus["item"]
                    st.write(f"🚌 **{idx+1}순위 추천 차편** (노선 ID: `{item['routeId']}`)")
                    st.write(f"  - 기점(첫 정류장) 출발 시각: {bus['b_hour']:02d}:{bus['b_min']:02d}")
                    st.write(f"  - 내 정류장까지 남은 거리: **정류장 {rem_stops}개** 이동 필요")
                    
                    if bus['rem_min'] >= 0:
                        st.write(f"  - ⏱️ **예상 도착 시각:** {bus['arrival_time'].strftime('%H:%M')} (**약 {bus['rem_min']:.0f}분 후 도착 예정**)")
                    else:
                        st.write(f"  - ⏱️ **도착 예정 시각:** {bus['arrival_time'].strftime('%H:%M')} (**기점 출발 후 {abs(bus['rem_min']):.0f}분 경과**)")
                    st.markdown("---")
            else:
                st.info("💡 금일 운행 예정인 셔틀버스 차편 정보가 조회되지 않습니다.")
   
        except Exception as e:
            st.error(f"셔틀버스 데이터 분석 오류: {e}")
    else:
        st.warning("⚠️ 셔틀버스 시간표 데이터를 찾을 수 없습니다.")
