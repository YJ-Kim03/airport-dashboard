#!/bin/bash

# 🔥 리눅스 커널이 UTC 기준이어도, date 명령어 실행 시 한국 시각(KST)을 강제로 반환하게 만듭니다.
TODAY=$(TZ="Asia/Seoul" date +"%Y-%m-%d")
NOW_TIME=$(TZ="Asia/Seoul" date +"%H%M")
SAVE_DIR="$HOME/airport_pipeline/data/$TODAY"

mkdir -p "$SAVE_DIR"

# 실행 시 전달받은 첫 번째 인자($1)에 따라 분기 처리
case "$1" in
    "congestion")
        # 출국장 혼잡도 API 호출 로직만 실행
        fetch_api "$CONGESTION_URL" "departure_congestion"
        ;;
    "parking")
        # 주차 정보 API 호출 로직만 실행
        fetch_api "$PARKING_URL" "parking_info"
        ;;
    "shuttle")
        # 셔틀버스 출도착 API 호출 로직 실행
        fetch_api "$SHUTTLE_DEP_URL" "shuttle_bus_departure"
        fetch_api "$SHUTTLE_ARR_URL" "shuttle_bus_arrival"
        ;;
    "forecast")
        # 승객 예보 API 호출 로직만 실행
        fetch_api "$PASSGR_URL" "passenger_forecast"
        ;;
    "all")
        # 전체 API 일괄 호출 (테스트용)
        ;;
    *)
        echo "사용법: $0 {congestion|parking|shuttle|forecast|all}"
        exit 1
        ;;
esac

# 1. 날짜 및 시간 변수 설정
TODAY=$(date +"%Y-%m-%d")
NOW_TIME=$(date +"%H%M")
SAVE_DIR="$HOME/airport_pipeline/data/$TODAY"

# 폴더가 없으면 자동 생성
mkdir -p "$SAVE_DIR"

SERVICE_KEY="e73b32a2c64cf691547315dc0c89769dc8f049a4f702adbdf6261d3ac5d752d1"

echo "🛫 [$(date +"%Y-%m-%d %H:%M:%S")] 인천공항 API 통합 수집 시작..."

# 2. API 호출 및 저장 함수 (에러 핸들링 및 로깅 적용)
fetch_api() {
    local url=$1
    local filename=$2
    local target_file="$SAVE_DIR/${filename}_$NOW_TIME.json"
    local error_file="$SAVE_DIR/${filename}_error_$NOW_TIME.log"
    local raw_response

    # API 서버로부터 원본 응답을 먼저 변수에 받아옵니다.
    raw_response=$(curl -s -X GET "$url")

    # 수신된 데이터가 정상적인 JSON 구조인지 jq로 우선 검증합니다.
    if echo "$raw_response" | jq . >/dev/null 2>&1; then
        # 검증에 성공하면 정렬하여 json 파일로 저장합니다.
        echo "$raw_response" | jq . > "$target_file"
        echo " ✔️ $filename 데이터 저장 완료"
    else
        # JSON 파싱에 실패한 경우 (XML 에러 메시지 등)
        echo " ❌ $filename 데이터 수집 실패! (API 서버 에러 또는 권한 문제)"
        echo "    👉 원본 응답 요약: $(echo "$raw_response" | head -c 200)..."
        
        # 원본 에러 텍스트를 .log 파일로 별도 저장하여 원인 파악을 돕습니다.
        echo "$raw_response" > "$error_file"
        echo "    📂 상세 에러 로그 저장됨: $error_file"
    fi
}

# 3. 4가지 핵심 API 수집 실행 (주차 정보 추가 완료)

# ① 승객예고 (출·입국장별)
PASSGR_URL="https://apis.data.go.kr/B551177/passgrAnncmt/getPassgrAnncmt?serviceKey=$SERVICE_KEY&type=json"
fetch_api "$PASSGR_URL" "passenger_forecast"

# ② 출국장 혼잡도 조회
CONGESTION_URL="https://apis.data.go.kr/B551177/statusOfDepartureCongestion/getDepartureCongestion?serviceKey=$SERVICE_KEY&type=json"
fetch_api "$CONGESTION_URL" "departure_congestion"

# ③-1. 셔틀버스 정보 (출발 노선)
SHUTTLE_DEP_URL="https://apis.data.go.kr/B551177/ShtbusInfo/getShtbTimeInfo?serviceKey=$SERVICE_KEY&type=json&numOfRows=500"
fetch_api "$SHUTTLE_DEP_URL" "shuttle_bus_departure"

# ③-2. 셔틀버스 정보 (도착 노선)
SHUTTLE_ARR_URL="https://apis.data.go.kr/B551177/ShtbusInfo/getShtbArrivalPredInfo?serviceKey=$SERVICE_KEY&type=json&numOfRows=500"
fetch_api "$SHUTTLE_ARR_URL" "shuttle_bus_arrival"

# ④ 주차 정보 (새로 추가된 부분!)
PARKING_URL="https://apis.data.go.kr/B551177/StatusOfParking/getTrackingParking?serviceKey=$SERVICE_KEY&type=json"
fetch_api "$PARKING_URL" "parking_info"

echo "✨ 통합 데이터 수집 완료!"


# ==========================================
# [시스템 프로그래밍 가산점] Streamlit Cloud 데이터 실시간 동기화 파이프라인
# ==========================================
cd ~/airport_pipeline
git add data/
git commit -m "auto: pipeline live data sync $(date +'%Y-%m-%d %H:%M')"
git push origin main

