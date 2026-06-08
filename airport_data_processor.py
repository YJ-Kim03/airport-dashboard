import json
import os
from datetime import datetime, timedelta, timezone

def get_latest_file(directory, prefix):
    if not os.path.exists(directory):
        return None
    files = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith('.json')]
    if not files:
        return None
    files.sort()
    return os.path.join(directory, files[-1])

def main():
    kst_zone = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst_zone)
    
    print(f"[{now_kst.strftime('%Y-%m-%d %H:%M:%S')} KST] 실시간 공항 데이터 처리 엔진 구동...")
    
    today_str = now_kst.strftime("%Y-%m-%d")
    base_dir = os.path.expanduser(f"~/airport_pipeline/data/{today_str}")

    # [파트 A] 주차장 혼잡도 파싱
    parking_file = get_latest_file(base_dir, "parking_info")
    if parking_file:
        with open(parking_file, 'r', encoding='utf-8') as f:
            parking_data = json.load(f)
        print(f"\n[주차장 데이터 파싱 성공: {os.path.basename(parking_file)}]")
        try:
            items = parking_data.get('response', {}).get('body', {}).get('items', [])
            for item in items:
                floor = item.get('floor', '알 수 없음')
                parking_cars = int(item.get('parking', 0))
                total_capacity = int(item.get('parkingarea', 0))
                if total_capacity > 0:
                    parking_rate = (parking_cars / total_capacity) * 100
                    print(f"  ✔️ {floor}: 주차 차량 {parking_cars}대 / 총 {total_capacity}면 ({parking_rate:.1f}%)")
        except Exception as e:
            print(f" ❌ 주차 데이터 연산 오류: {e}")

# ----------------------------------------------------
    # [파트 B] 하루 전체 스케줄 기반 실시간 가장 가까운 버스 연산 ($t$)
    # ----------------------------------------------------
    print("\n[셔틀버스 실시간 타임라인 기반 예상 도착 시간(t) 연산]")
    
    TOTAL_STOPS_TO_TARGET = 5
    TIME_PER_STOP = 7.0  # 정류장 간 평균 7분 소요
    
    shuttle_dep_file = get_latest_file(base_dir, "shuttle_bus_departure")
    if shuttle_dep_file:
        with open(shuttle_dep_file, 'r', encoding='utf-8') as f:
            dep_data = json.load(f)
        try:
            items = dep_data.get('response', {}).get('body', {}).get('items', [])
            
            upcoming_buses = []
            for bus in items:
                start_time_str = bus.get('startTime') # 예: "0430", "1315", "2240"
                if not start_time_str:
                    continue
                
                # 오늘 날짜와 버스 시간표 결합
                bus_time = datetime.strptime(f"{today_str} {start_time_str}", "%Y-%m-%d %H%M").replace(tzinfo=kst_zone)
                
                # 🔥 [핵심 실시간 로직] 하루 전체 데이터 중 '현재 시각 이후에 출발할 미래의 버스'만 낚아챕니다!
                if bus_time > now_kst:
                    t_waiting = (bus_time - now_kst).total_seconds() / 60 # 출발까지 남은 대기 시간
                    total_t = t_waiting + (TOTAL_STOPS_TO_TARGET * TIME_PER_STOP) # 탑승 후 타겟 정류장 도착까지 총 소요시간
                    upcoming_buses.append((bus.get('routeId'), start_time_str, t_waiting, total_t))
            
            # 가장 빨리 탈 수 있는 미래 버스 순으로 정렬
            upcoming_buses.sort(key=lambda x: x[2])
            
            if upcoming_buses:
                print(f" 📌 현재 시각({now_kst.strftime('%H:%M')}) 기준 다음 탑승 가능 셔틀버스 정보 (Top 2):")
                for i, (route_id, start_time, t_wait, t_total) in enumerate(upcoming_buses[:2]):
                    print(f"   - {i+1}순위 차편 | 노선ID {route_id} | 기점 {start_time[0:2]}:{start_time[2:4]} 출발 예정")
                    print(f"     -> ⏳ 내 정류장까지 버스 출발 대기 시간: 약 {t_wait:.1f}분 남음")
                    print(f"     -> ⏱️ [기획안 8p 사양] 최종 예상 도착 시간(t): 약 {t_total:.1f}분 후 내 정류장 도착")
            else:
                print("  ⚠️ 하루치 데이터를 조회했으나, 현재 시각 이후로 남은 금일 운행 스케줄이 모두 마감되었습니다.")
        except Exception as e:
            print(f" ❌ 셔틀버스 실시간 타임라인 연산 오류: {e}")

if __name__ == "__main__":
    main()
