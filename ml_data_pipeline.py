import os
import glob
import json
import pandas as pd

def load_and_merge_json_files(base_dir, api_name):
    combined_records = []
    # 데이터 폴더 내의 모든 날짜 디렉터리 내부를 탐색
    search_path = os.path.join(base_dir, "data", "*", f"{api_name}_*.json")
    file_list = glob.glob(search_path)
    
    print(f"🔍 [{api_name}] 데이터 탐색 중... 총 {len(file_list)}개의 파일을 찾았습니다.")
    
    if not file_list:
        return pd.DataFrame()
        
    for file_path in sorted(file_list):
        try:
            if os.path.getsize(file_path) == 0:
                continue
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # API 고유의 response -> body -> items 구조 파싱
            items = data.get("response", {}).get("body", {}).get("items", [])
            
            # 리스트와 딕셔너리 예외 처리
            if isinstance(items, list):
                combined_records.extend(items)
            elif isinstance(items, dict):
                combined_records.append(items)
        except Exception as e:
            continue
            
    return pd.DataFrame(combined_records)

if __name__ == "__main__":
    BASE_DIR = os.path.expanduser("~/airport_pipeline")
    print("🚀 데이터 일괄 통합 파이프라인 가동...")
    
    # 크론탭으로 수집할 때 설정한 파일명 접두사(Prefix)를 적어주세요.
    # 만약 수집 스크립트에서 다르게 설정했다면 "departure_congestion" 부분을 실제 파일명에 맞게 수정해야 합니다.
    df_congestion = load_and_merge_json_files(BASE_DIR, "departure_congestion")
    
    if not df_congestion.empty:
        df_congestion.to_csv(os.path.join(BASE_DIR, "master_congestion.csv"), index=False, encoding='utf-8-sig')
        print("💾 master_congestion.csv 생성 완료!")
    else:
        print("❌ 통합할 데이터가 없습니다. 크론탭으로 모아둔 파일명 접두사가 'departure_congestion'이 맞는지 확인해 보세요.")
