# 토지 분석 자동화 시스템 제안서

## 목표
토지 정보(위치, 면적 등)를 입력하면 NHO-PD 스타일의 종합 분석 리포트를 자동 생성하는 시스템 구축

---

## 1. 현재 Output 리포트 분석

### 기존 리포트 구조 (5개 샘플)

| 리포트 | 토지 | 페이지 | 주요 내용 |
|--------|------|--------|-----------|
| HP-35ha_Proposal | Hai Phong 35ha | 109p | 시장 분석, 개발 전략, SWOT, 경쟁사 비교, 가격 전략 |
| BD_Potential_Land_Review | Binh Duong 3개 토지 | 17p | 3개 부지 비교, 시장 현황, 개발 추천 |
| Hai_Phong_3_Land_SWOT | Hai Phong 3개 토지 | 1p | SWOT 비교표 |
| 25ha_Duong_Kinh | Hai Phong 25ha | 12p | 세부 분석, 경쟁사, 가격 |
| 240ha_Bac_Ninh | Bac Ninh 240ha | 43p | Mega 프로젝트, 단계별 개발 전략 |

### 리포트 공통 섹션

1. **Executive Summary** (3-5p)
   - 토지 개요
   - 핵심 발견사항
   - 추천 개발 전략

2. **Location Analysis** (5-10p)
   - 지리적 위치 (도시, 구, 동)
   - 접근성 (도로, 공항, 항구)
   - 인프라 현황
   - 주변 개발 현황

3. **Market Analysis** (10-20p)
   - 도시 시장 개요
   - 공급-수요 현황
   - 가격 트렌드
   - 경쟁사 프로젝트
   - 시장 세그먼트 분석

4. **Site Analysis** (10-15p)
   - 토지 면적 및 형태
   - 용도지역 (Land use)
   - 개발 잠재력
   - 제약사항

5. **Competitor Benchmarking** (10-20p)
   - 인근 경쟁 프로젝트 (5-10개)
   - 가격 비교
   - 제품 믹스 비교
   - 판매 성과

6. **Development Strategy** (10-15p)
   - 추천 개발 타입 (Mixed-use, Residential, etc.)
   - 제품 믹스 (Apt, TH, SH, Villa 비율)
   - 단계별 개발 계획
   - 타겟 세그먼트 (Grade)

7. **Financial Analysis** (10-15p)
   - 벤치마크 가격
   - 가격 전략
   - 수익성 분석
   - 판매 시뮬레이션

8. **SWOT Analysis** (2-5p)
   - Strengths
   - Weaknesses
   - Opportunities
   - Threats

9. **Recommendations** (3-5p)
   - 개발 우선순위
   - 리스크 완화 방안
   - 다음 단계

---

## 2. 필요한 입력 정보

### 기본 정보 (필수)
```python
land_input = {
    # 위치 정보
    "city": "Ho Chi Minh City",           # 도시
    "district": "District 2",              # 구
    "ward": "Thao Dien",                   # 동 (선택)
    "address": "123 Nguyen Van Huong",     # 주소
    "coordinates": {                        # 좌표 (선택)
        "lat": 10.8068,
        "lng": 106.7372
    },

    # 토지 정보
    "land_area_ha": 35.0,                  # 면적 (hectare)
    "land_use": "residential",             # 용도지역
    "ownership": "private",                # 소유권 현황

    # 개발 목표
    "target_segment": "M-I",               # 타겟 등급
    "development_type": "mixed-use",       # 개발 타입
    "budget_usd": 50000000,                # 예산 (선택)
}
```

### 추가 정보 (선택)
```python
optional_input = {
    # 인프라
    "distance_to_cbd_km": 5.0,             # CBD까지 거리
    "distance_to_airport_km": 15.0,        # 공항까지 거리
    "metro_station": "Thao Dien Station",  # 인근 지하철역
    "major_roads": ["Hanoi Highway"],      # 주요 도로

    # 제약사항
    "constraints": [
        "Height limit: 25 floors",
        "Green space requirement: 30%"
    ],

    # 우선순위
    "priorities": [
        "fast_sales",      # 빠른 판매
        "premium_brand",   # 프리미엄 브랜드
        "phased_dev"       # 단계적 개발
    ]
}
```

---

## 3. 자동화 시스템 아키텍처

### 3.1 입력 레이어
```
┌─────────────────────────────────┐
│  Input Interface                │
│  - Web Form / CLI / API         │
│  - 토지 정보 수집               │
│  - 유효성 검증                  │
└─────────────────────────────────┘
           ↓
```

### 3.2 데이터 수집 레이어
```
┌─────────────────────────────────┐
│  Data Collection Engine         │
│  - 도시 시장 데이터 조회        │
│  - 경쟁사 프로젝트 검색         │
│  - 가격 벤치마크 수집           │
│  - 인프라 정보 매핑             │
└─────────────────────────────────┘
           ↓
```

### 3.3 분석 레이어
```
┌─────────────────────────────────┐
│  Analysis Engine                │
│  - 시장 분석                    │
│  - 경쟁사 비교                  │
│  - 개발 전략 생성               │
│  - SWOT 분석                    │
│  - 재무 시뮬레이션              │
└─────────────────────────────────┘
           ↓
```

### 3.4 리포트 생성 레이어
```
┌─────────────────────────────────┐
│  Report Generation              │
│  - Jinja2 템플릿 렌더링         │
│  - 차트 생성                    │
│  - PDF 출력                     │
└─────────────────────────────────┘
```

---

## 4. 구현 단계별 계획

### Phase 1: 데이터 준비 (1-2주)

**1.1 참조 데이터 확장**
```bash
# 추가 필요 데이터
data/seed/infrastructure.json      # 인프라 정보
data/seed/land_use_zones.json      # 용도지역 규정
data/seed/development_costs.json   # 개발 비용 벤치마크
data/seed/market_benchmarks.json   # 시장 벤치마크
```

**1.2 지리 데이터**
```python
# cities.json 확장
{
  "id": 1,
  "name_en": "Ho Chi Minh City",
  "cbd_location": {"lat": 10.7769, "lng": 106.7009},
  "airport_location": {"lat": 10.8188, "lng": 106.6519},
  "metro_lines": [
    {"line": 1, "stations": [...]}
  ]
}
```

**1.3 경쟁사 데이터베이스 강화**
- 모든 프로젝트에 좌표 추가
- 인근 프로젝트 검색 알고리즘
- 유사 프로젝트 매칭 로직

### Phase 2: 분석 엔진 개발 (2-3주)

**2.1 위치 분석 모듈**
```python
# src/analysis/location_analyzer.py

def analyze_location(land_input: dict) -> dict:
    """
    토지 위치 분석
    - CBD 접근성 점수
    - 인프라 점수
    - 개발 잠재력 평가
    """
    return {
        "cbd_accessibility": 8.5,
        "infrastructure_score": 7.2,
        "development_potential": "High",
        "nearby_landmarks": [...]
    }
```

**2.2 시장 분석 모듈**
```python
# src/analysis/market_analyzer.py

def analyze_market(city: str, district: str, segment: str) -> dict:
    """
    시장 분석 - 기존 DB 데이터 활용
    - 지역 공급-수요
    - 가격 트렌드
    - 흡수율
    """
    return {
        "supply_units": 5000,
        "absorption_rate": 72.5,
        "avg_price": 3200,
        "market_outlook": "Strong demand"
    }
```

**2.3 경쟁사 비교 모듈**
```python
# src/analysis/competitor_finder.py

def find_competitors(
    location: dict,
    radius_km: float,
    segment: str,
    limit: int = 10
) -> list:
    """
    인근 경쟁 프로젝트 검색
    - 거리 기반 필터링
    - 세그먼트 유사도
    - 11-dimension 비교
    """
    return [
        {"name": "Project A", "distance_km": 2.5, ...},
        ...
    ]
```

**2.4 개발 전략 생성**
```python
# src/analysis/strategy_generator.py

def generate_strategy(
    land_input: dict,
    market_data: dict,
    competitors: list
) -> dict:
    """
    최적 개발 전략 생성
    - 제품 믹스 추천
    - 단계별 개발 계획
    - 가격 전략
    """
    return {
        "recommended_type": "mixed-use",
        "product_mix": {
            "apartment": 70,
            "townhouse": 20,
            "shophouse": 10
        },
        "phasing": [...],
        "pricing_strategy": {...}
    }
```

### Phase 3: 리포트 템플릿 개발 (2주)

**3.1 템플릿 구조**
```
templates/
├── land_review/
│   ├── executive_summary.md.j2
│   ├── location_analysis.md.j2
│   ├── market_analysis.md.j2
│   ├── site_analysis.md.j2
│   ├── competitor_benchmark.md.j2
│   ├── development_strategy.md.j2
│   ├── financial_analysis.md.j2
│   ├── swot_analysis.md.j2
│   └── recommendations.md.j2
├── land_review_full.md.j2      # Master template
└── land_review_summary.md.j2    # 요약본
```

**3.2 차트 생성**
```python
# src/reports/land_review_charts.py

def location_map(coordinates: dict, competitors: list) -> str:
    """토지 위치 + 경쟁사 지도"""

def price_comparison_chart(land_price: float, competitors: list) -> str:
    """가격 비교 차트"""

def development_phasing_gantt(phases: list) -> str:
    """개발 단계 Gantt 차트"""

def market_supply_demand(market_data: dict) -> str:
    """공급-수요 차트"""
```

### Phase 4: 통합 및 인터페이스 (1-2주)

**4.1 커맨드 라인 인터페이스**
```bash
# 기본 사용
python -m src.commands.land_review \
    --city "HCMC" \
    --district "District 2" \
    --area-ha 35 \
    --segment "M-I" \
    --output report.md

# JSON 입력 파일 사용
python -m src.commands.land_review \
    --input land_data.json \
    --output report.pdf
```

**4.2 웹 인터페이스 (선택)**
```python
# app.py - Streamlit or Flask

import streamlit as st

st.title("토지 분석 리포트 생성기")

# 입력 폼
city = st.selectbox("도시", ["HCMC", "Hanoi", "Binh Duong"])
district = st.text_input("구/군")
area_ha = st.number_input("면적 (ha)", min_value=0.1)

if st.button("리포트 생성"):
    report = generate_land_review({...})
    st.download_button("PDF 다운로드", report)
```

**4.3 슬래시 커맨드**
```bash
/land-review \
    --city HCMC \
    --district "District 2" \
    --area 35 \
    --segment M-I
```

---

## 5. 데이터 준비 체크리스트

### 5.1 필수 데이터
- [ ] **인프라 데이터**
  - [ ] 지하철역 위치 및 노선
  - [ ] 주요 도로망
  - [ ] 공항, 항구 위치
  - [ ] 쇼핑몰, 학교, 병원

- [ ] **용도지역 규정**
  - [ ] 도시별 용도지역 코드
  - [ ] 건폐율, 용적률 제한
  - [ ] 층수 제한
  - [ ] 녹지 비율 요구사항

- [ ] **개발 비용**
  - [ ] 건설 비용 (타입별)
  - [ ] 인프라 비용
  - [ ] 마케팅 비용
  - [ ] 금융 비용

- [ ] **시장 벤치마크**
  - [ ] 등급별 가격 범위
  - [ ] 판매 속도 벤치마크
  - [ ] 제품 믹스 트렌드

### 5.2 프로젝트 데이터 강화
- [ ] **좌표 추가**
  ```python
  # projects.json 확장
  {
    "id": 1,
    "name": "Masteri Thao Dien",
    "coordinates": {"lat": 10.8068, "lng": 106.7372},
    "year_completed": 2017,
    "absorption_rate_pct": 85.0
  }
  ```

- [ ] **개발 비용 추가**
  ```python
  {
    "construction_cost_usd_m2": 650,
    "land_cost_usd_m2": 1200,
    "total_investment_usd": 150000000
  }
  ```

### 5.3 참조 템플릿
- [ ] 기존 5개 리포트 구조 분석
- [ ] 섹션별 필수 요소 추출
- [ ] 차트 타입 정의
- [ ] 텍스트 템플릿 작성

---

## 6. 핵심 알고리즘

### 6.1 경쟁사 검색
```python
def find_nearby_projects(
    location: tuple[float, float],  # (lat, lng)
    radius_km: float,
    filters: dict
) -> list[Project]:
    """
    Haversine 공식으로 거리 계산
    필터: segment, price_range, status
    """
    from math import radians, cos, sin, asin, sqrt

    def haversine(lon1, lat1, lon2, lat2):
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km

    # 모든 프로젝트 검색
    all_projects = session.query(Project).all()

    nearby = []
    for project in all_projects:
        if not project.coordinates:
            continue

        distance = haversine(
            location[1], location[0],
            project.coordinates['lng'], project.coordinates['lat']
        )

        if distance <= radius_km:
            if matches_filters(project, filters):
                nearby.append({
                    "project": project,
                    "distance_km": distance
                })

    return sorted(nearby, key=lambda x: x['distance_km'])
```

### 6.2 개발 전략 최적화
```python
def optimize_product_mix(
    land_area_ha: float,
    target_segment: str,
    market_data: dict
) -> dict:
    """
    최적 제품 믹스 계산
    - 시장 수요 기반
    - 수익성 최대화
    - 리스크 분산
    """
    # 세그먼트별 선호도
    preferences = {
        "H-I": {"apt": 60, "th": 30, "sh": 10},
        "M-I": {"apt": 70, "th": 20, "sh": 10},
        "A-I": {"apt": 80, "th": 15, "sh": 5}
    }

    # 면적 기반 조정
    if land_area_ha > 50:
        # 대규模 - 믹스 다양화
        mix = preferences[target_segment]
    else:
        # 소규模 - 단순화
        mix = {"apt": 90, "th": 10, "sh": 0}

    return {
        "product_mix": mix,
        "total_units": calculate_units(land_area_ha, mix),
        "phasing": generate_phasing(land_area_ha)
    }
```

### 6.3 가격 전략
```python
def generate_pricing_strategy(
    target_segment: str,
    competitors: list,
    location_score: float
) -> dict:
    """
    경쟁력 있는 가격 전략
    """
    # 경쟁사 평균
    comp_avg = sum(c['price_usd'] for c in competitors) / len(competitors)

    # 위치 프리미엄
    location_premium = 1.0 + (location_score - 5.0) * 0.05

    # 추천 가격
    recommended_price = comp_avg * location_premium

    return {
        "recommended_price_usd_m2": recommended_price,
        "price_range": {
            "min": recommended_price * 0.95,
            "max": recommended_price * 1.10
        },
        "positioning": "aligned" if abs(comp_avg - recommended_price) < 200 else "premium"
    }
```

---

## 7. 샘플 출력 구조

### 7.1 리포트 목차
```markdown
# Land Review: [Location] - [Area]ha

## Executive Summary (5p)
- Project Overview
- Key Findings
- Recommendations

## 1. Location Analysis (10p)
- Geographic Position
- Accessibility (CBD, Airport, Major Roads)
- Infrastructure Development
- Surrounding Amenities

## 2. Market Analysis (15p)
- City Market Overview
- District Performance
- Supply-Demand Dynamics
- Price Trends
- Market Segment Analysis

## 3. Site Analysis (10p)
- Land Specifications
- Development Potential
- Zoning Regulations
- Constraints & Opportunities

## 4. Competitor Benchmarking (20p)
- Nearby Projects (5-10)
- Price Comparison
- Product Mix Comparison
- Sales Performance
- Competitive Positioning

## 5. Development Strategy (15p)
- Recommended Development Type
- Product Mix Optimization
- Phasing Plan
- Target Market Segments

## 6. Financial Analysis (15p)
- Benchmark Pricing
- Revenue Projection
- Cost Estimation
- Profitability Analysis
- Sensitivity Analysis

## 7. SWOT Analysis (5p)
- Strengths
- Weaknesses
- Opportunities
- Threats

## 8. Recommendations (5p)
- Go/No-Go Decision
- Development Priorities
- Risk Mitigation
- Next Steps

## Appendix
- Data Sources
- Assumptions
- Detailed Tables
```

---

## 8. 구현 우선순위

### High Priority (즉시 시작)
1. **프로젝트 좌표 데이터 추가** (1일)
2. **경쟁사 검색 알고리즘** (2-3일)
3. **기본 템플릿 작성** (3-4일)
4. **CLI 인터페이스** (2일)

### Medium Priority (1-2주 내)
5. **시장 분석 자동화** (3-4일)
6. **개발 전략 생성** (3-4일)
7. **차트 생성** (2-3일)
8. **PDF 출력** (2일)

### Low Priority (추후)
9. **웹 인터페이스** (1주)
10. **재무 시뮬레이션** (1주)
11. **지도 시각화** (3-4일)

---

## 9. 예상 결과물

### 입력
```python
land_input = {
    "city": "Ho Chi Minh City",
    "district": "District 2",
    "land_area_ha": 35.0,
    "target_segment": "M-I",
    "development_type": "mixed-use"
}
```

### 출력
- **리포트 파일**: `land_review_district2_35ha.md` (80-100 페이지)
- **PDF 버전**: `land_review_district2_35ha.pdf`
- **데이터 파일**: `land_review_district2_35ha_data.json`
- **생성 시간**: 2-5분

---

## 10. 다음 단계

1. **의사결정**: 위 제안 검토 및 우선순위 확정
2. **데이터 수집**: 프로젝트 좌표, 인프라 데이터 수집
3. **프로토타입**: Phase 1 기능 구현 (경쟁사 검색 + 기본 템플릿)
4. **테스트**: 샘플 토지로 리포트 생성
5. **반복**: 피드백 기반 개선

**시작하시겠습니까?** 어떤 Phase부터 진행할지 알려주시면 바로 시작하겠습니다!
