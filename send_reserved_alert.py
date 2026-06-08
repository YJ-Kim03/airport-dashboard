print("DEBUG: 알림 스크립트가 실행되었습니다.") # 최상단에 추가
import json
import requests
import datetime
import os

# 1. 파일 경로 설정 (app.py와 반드시 같아야 함!)
ALERT_DB_PATH = "/home/maengju/airport_pipeline/user_alerts.json"

# 2. 텔레그램 알림 발송 함수
def send_telegram_message(chat_id, message):
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE" # 여기에 본인의 봇 토큰 입력!
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

# 3. 알림 체크 및 발송 로직
if os.path.exists(ALERT_DB_PATH):
    with open(ALERT_DB_PATH, "r", encoding="utf-8") as f:
        alerts = json.load(f)

    now = datetime.datetime.now().strftime("%H:%M")
    
    for alert in alerts:
        # 시간이 되었고, 아직 안 보냈다면
        if alert.get("target_time") == now and not alert.get("sent", False):
            send_telegram_message(alert["chat_id"], "[인천공항 알림] 설정하신 시간이 되었습니다!")
            alert["sent"] = True # 발송 표시

    # 결과 저장
    with open(ALERT_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=4)
