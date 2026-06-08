import requests

TOKEN = "8925194718:AAGqy1koGohvlgyuEGxDDCvJAmFjTQliTM4"
CHAT_ID = "8954218615"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def test_send():
    text = "🚀 [디버그 테스트] 봇이 정상 작동 중입니다."
    params = {'chat_id': CHAT_ID, 'text': text}
    try:
        response = requests.post(BASE_URL, params=params)
        if response.status_code == 200:
            print("✅ 메시지 전송 성공!")
        else:
            print(f"❌ 전송 실패: {response.text}")
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    test_send()
