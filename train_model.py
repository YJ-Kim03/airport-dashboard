import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

def load_master_data(base_dir):
    """
    1단계: 이전 단계에서 결합하여 저장한 master_congestion.csv를 로드합니다.
    """
    csv_path = os.path.join(base_dir, "master_congestion.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"❌ 마스터 데이터 파일이 없습니다: {csv_path}\n먼저 데이터 통합 스크립트를 실행하세요.")
    
    df = pd.read_csv(csv_path)
    print(f"📈 데이터 로드 완료: 총 {len(df)}개의 행")
    return df

def feature_engineering(df):
    """
    2단계: 피처 엔지니어링 (원시 데이터로부터 학습에 필요한 단서들을 추출)
    """
    # 결측치 처리 (대기 시간이 없는 데이터는 제거하거나 0으로 채움)
    df = df.dropna(subset=['waitTime'])
    
    # 시간 기반 피처 생성 (정합성을 위해 datetime 변환)
    # API 응답 내 기준 시간 컬럼명(예: occurtime 또는 cgstTm)에 맞게 수정 필요
    time_col = 'occurtime' if 'occurtime' in df.columns else df.columns[0]
    df['datetime'] = pd.to_datetime(df[time_col], errors='coerce')
    df = df.dropna(subset=['datetime'])
    
    df['hour'] = df['datetime'].dt.hour
    df['minute'] = df['datetime'].dt.minute
    df['day_of_week'] = df['datetime'].dt.dayofweek  # 월:0, 일:6
    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
    
    # 문자열로 된 공항 구역/터미널 정보가 있다면 원-핫 인코딩(One-Hot Encoding)
    # 예: 터미널구분(terminalId) 또는 게이트명 등
    if 'terminalId' in df.columns:
        df = pd.get_dummies(df, columns=['terminalId'], drop_first=True)
        
    # 수치형 변수 타입 강제 변환
    df['waitLength'] = pd.to_numeric(df['waitLength'], errors='coerce').fillna(0)
    
    # 학습에 사용할 특성(X)과 정답지(y) 정의
    # 프로젝트 환경에 맞는 실제 컬럼명으로 매핑해야 합니다.
    feature_cols = ['hour', 'minute', 'day_of_week', 'is_weekend', 'waitLength']
    # 원-핫 인코딩된 컬럼들도 특성에 추가
    feature_cols += [col for col in df.columns if 'terminalId_' in col]
    
    X = df[feature_cols]
    y = df['waitTime']  # Target: 예측하고자 하는 출국장 대기 시간(분)
    
    print(f"🧩 피처 엔지니어링 완료! 사용된 특성 변수들: {feature_cols}")
    return X, y

def train_and_evaluate(X, y, base_dir):
    """
    3단계: 데이터 분할, 모델 학습 및 평가지표 출력
    """
    # 학습 데이터와 검증 데이터 분할 (8:2)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("🤖 머신러닝 모델(RandomForest) 학습 시작...")
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    print("✅ 모델 학습 완료!")
    
    # 4단계: 모델 평가
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print("\n=========================================")
    print(f"📊 [모델 평가 결과]")
    print(f" - 평균 절대 오차 (MAE): {mae:.2f}분")
    print(f" - 모델 설명력 (R² Score): {r2:.4f}")
    print("=========================================\n")
    
    # 5단계: 가상환경 내 모델 파일 내보내기 (Pickling)
    model_path = os.path.join(base_dir, "saved_models", "congestion_predict_model.pkl")
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    joblib.dump(model, model_path)
    print(f"💾 모델 파일 저장 완료 -> {model_path}")

if __name__ == "__main__":
    BASE_DIR = os.path.expanduser("~/airport_pipeline")
    
    try:
        # 파이프라인 순차 실행
        raw_df = load_master_data(BASE_DIR)
        X, y = feature_engineering(raw_df)
        train_and_evaluate(X, y, BASE_DIR)
        
    except Exception as e:
        print(f"❌ 학습 중 오류 발생: {e}")
