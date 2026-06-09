import json
import glob
import os
from datetime import datetime, timedelta
import requests
import pytz

KST = pytz.timezone('Asia/Seoul')

ALERT_DB_PATH = "/home/maengju/airport_pipeline/user_alerts.json"
TOKEN = "8925194718:AAGqy1koGohvlgyuEGxDDCvJAmFjTQliTM4"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def get_latest_parking_data():
    today = datetime.now().strftime("%Y-%m-%d")
    search_path = f"/home/maengju/airport_pipeline/data/{today}/parking_info_*.json"
    files = sorted(glob.glob(search_path))
    if not files:
        return None
    
    try:
        with open(files[-1], 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 1. API 구조 확인 (항목이 리스트인 곳을 찾음)
            if isinstance(data, dict):
                # 공공데이터 API 구조를 고려해 items를 찾아감
                response = data.get('response', {})
                body = response.get('body', {})
                items = body.get('items', [])
                return items if isinstance(items, list) else []
            return []
    except Exception as e:
        print(f"데이터 파싱 오류: {e}")
        return []

def send_telegram_msg(chat_id, text):
    params = {'chat_id': chat_id, 'text': text}
    requests.post(BASE_URL, params=params)

def main():
    if not os.path.exists(ALERT_DB_PATH) or os.path.getsize(ALERT_DB_PATH) == 0:
        return

    with open("/home/maengju/airport_pipeline/user_alerts.json", "r", encoding="utf-8") as f:
        alerts = json.load(f)

    current_time_str = datetime.now(KST).strftime("%H:%M")
    parking_items = get_latest_parking_data()
    
    updated = False

    for alert in alerts:
#        if not alert.get('sent', False) and current_time_str >= alert.get('target_time', '99:99'):
        if True: 
            msg = f"🚀 [인천공항 실시간 주차 현황]\n"
            if parking_items and isinstance(parking_items, list):
                for item in parking_items:
                    name = item.get('floor', '구역명 미상')
                    available = int(item.get('parking', 0))       # 현재 남은 자리
                    total = int(item.get('parkingarea', 1))       # 전체 면수 (0 나누기 방지 위해 최소 1)
                    
                    occupied = total - available
                    percentage = (occupied / total) * 100
                    
                    msg += f"📍 {name} : {available}대 가능 ({percentage:.1f}%)\n"
            else:
                msg += "현재 실시간 주차 데이터를 불러올 수 없습니다."

            send_telegram_msg(alert['chat_id'], msg)
            alert['sent'] = True 
            updated = True
            print(f"알림 발송 완료: {alert['target_time']}")

    if updated:
        with open(ALERT_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(alerts, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    print(f"DEBUG: 서버가 인식한 현재 KST 시각: {datetime.now(pytz.timezone('Asia/Seoul')).strftime('%H:%M')}")
    main()

