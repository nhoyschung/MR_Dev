# 데이터 수집 자동화 시스템

## 개요
NHO-PD 시장조사 리포트 PDF를 자동으로 수집, 처리, DB 저장하는 시스템

## 완성된 기능

### ✅ Phase 1: Core Pipeline (Tasks #17-21 완료)

#### 1. PDF 메타데이터 추출기 (`src/collectors/pdf_metadata.py`)
- **기능**: PDF 파일에서 구조화된 메타데이터 추출
- **추출 정보**:
  - 파일 정보: 파일명, 크기, 생성/수정 시간
  - PDF 속성: 페이지 수, 제목, 저자, 생성 날짜
  - 자동 추론: 리포트 타입, 도시, 기간, 날짜 (파일명 기반)

**파일명 패턴 인식**:
```python
20251117_NHO-PD_2025 HCMC Market Analysis.pdf
→ {
    "inferred_date": "2025-11-17",
    "inferred_report_type": "market_analysis",
    "inferred_city": "Ho Chi Minh City",
    "inferred_period": "2025-H2"
}
```

**테스트 결과** (6개 PDF):
| 파일 | 크기 | 페이지 | 타입 | 도시 | 기간 |
|------|------|--------|------|------|------|
| Sales Price Analysis | 3.3MB | 66 | price_analysis | N/A | 2024-H1 |
| Developer Analysis | 14.9MB | 109 | developer_analysis | N/A | 2025-H1 |
| Binh Duong Market | 49.0MB | 241 | market_analysis | Binh Duong | 2025-H2 |
| HCMC Market | 40.0MB | 258 | market_analysis | HCMC | 2025-H2 |
| Mixed use Case study | 11.5MB | 36 | case_study | N/A | 2025-H2 |
| Hanoi Market | 81.9MB | 455 | market_analysis | Hanoi | 2026-H1 |

---

#### 2. PDF 텍스트 추출 서비스 (`src/collectors/pdf_extractor.py`)
- **기능**: PyMuPDF를 사용한 다중 패스 텍스트 추출
- **전략**:
  - **Full 모드** (<100 페이지): 전체 텍스트를 하나의 파일로 추출
  - **Multi-Pass 모드** (>100 페이지): 3개 파일로 분할
    - Pass 1: 1-20페이지 (개요/요약)
    - Pass 2: 21-60페이지 (중간 상세)
    - Pass 3: 61+페이지 (심층 섹션)

**테스트 결과**:
- 36페이지 PDF: 0.08초 (full 모드)
- 455페이지 PDF: 1.19초 (multi-pass 모드, 3개 파일 생성)
- 품질 점수: 텍스트 밀도 기반 (0-1)

---

#### 3. 데이터베이스 스키마 확장
**`source_reports` 테이블에 8개 컬럼 추가**:
```sql
ALTER TABLE source_reports ADD COLUMN pdf_path TEXT;
ALTER TABLE source_reports ADD COLUMN file_size_mb REAL;
ALTER TABLE source_reports ADD COLUMN pdf_created_at DATETIME;
ALTER TABLE source_reports ADD COLUMN extraction_started_at DATETIME;
ALTER TABLE source_reports ADD COLUMN extraction_completed_at DATETIME;
ALTER TABLE source_reports ADD COLUMN extraction_time_sec REAL;
ALTER TABLE source_reports ADD COLUMN quality_score REAL;
ALTER TABLE source_reports ADD COLUMN extracted_text_length INTEGER;
```

---

#### 4. 수집 오케스트레이터 (`src/collectors/orchestrator.py`)
- **기능**: 전체 파이프라인을 조율하는 중앙 관리자
- **워크플로우**:
  1. PDF 스캔 → 신규 파일 식별
  2. 메타데이터 추출
  3. DB에 레코드 생성 (status: pending)
  4. 텍스트 추출 (auto 전략)
  5. DB 업데이트 (status: extracted)

**상태 흐름**:
```
pending → extracting → extracted → ingested → error
```

**사용 예시**:
```python
from src.collectors.orchestrator import IngestionOrchestrator

# 초기화
orchestrator = IngestionOrchestrator(
    watch_dir='user_resources/D_colect',
    extracted_text_dir='user_resources/D_colect/extracted'
)

# 신규 PDF 스캔
from src.db.connection import get_session
with get_session() as session:
    new_pdfs = orchestrator.scan_for_new_pdfs(session)
    print(f"Found {len(new_pdfs)} new PDFs")

# 단일 PDF 수집
report = orchestrator.ingest_pdf(pdf_path, session)

# 전체 스캔 & 수집
results = orchestrator.scan_and_ingest()
```

---

## 현재 데이터 상태

### Before (기존)
- ❌ PDF 파일 미추적 (텍스트 파일만 DB에 기록)
- ❌ 메타데이터 누락 (page_count 모두 0)
- ❌ 수동 처리만 가능
- ✅ 19개 추출 텍스트 파일 (status: ingested)

### After (현재)
- ✅ PDF 파일 추적 (파일 경로, 크기, 생성일)
- ✅ 완전한 메타데이터 (페이지 수, 추출 시간, 품질 점수)
- ✅ 자동 파이프라인 (스캔 → 추출 → DB 저장)
- ✅ 20개 리포트 (19개 기존 + 1개 신규)

### 신규 수집 테스트 결과
```
File: 20251205_Mixed use development Case study.pdf
  - ID: 20
  - Type: case_study
  - Pages: 36
  - Size: 11.52 MB
  - Status: extracted
  - Quality: 27.5%
  - Extraction time: 0.08s
  - Text length: 19,789 chars
```

---

## 사용 방법

### 1. 단일 PDF 수집
```python
from src.collectors.orchestrator import ingest_single_pdf

result = ingest_single_pdf('user_resources/D_colect/report.pdf')
print(f"Ingested: {result['filename']} ({result['page_count']} pages)")
```

### 2. 폴더 스캔 & 일괄 수집
```python
from src.collectors.orchestrator import IngestionOrchestrator

orchestrator = IngestionOrchestrator('user_resources/D_colect')
results = orchestrator.scan_and_ingest()

print(f"Total: {results['total']}")
print(f"Success: {results['success']}")
print(f"Failed: {results['failed']}")
print(f"Skipped: {results['skipped']}")
```

### 3. 수집 상태 확인
```python
from src.collectors.orchestrator import IngestionOrchestrator
from src.db.connection import get_session

orchestrator = IngestionOrchestrator('user_resources/D_colect')

with get_session() as session:
    status = orchestrator.get_ingestion_status(session)
    print(f"PDFs in directory: {status['total_pdfs_in_directory']}")
    print(f"In database: {status['total_in_database']}")
    print(f"Breakdown: {status['status_breakdown']}")
```

---

## 다음 단계 (Phase 2-3)

### Phase 2: 자동화 (Task #22)
- [ ] 파일 시스템 감시자 (watchdog)
- [ ] 실시간 신규 파일 감지
- [ ] 자동 트리거 수집

### Phase 3: CLI & 모니터링 (Task #23)
- [ ] CLI 명령어:
  - `python -m src.collectors.ingest_pdf <file>`
  - `python -m src.collectors.scan_folder`
  - `python -m src.collectors.watch`
  - `python -m src.collectors.status`
- [ ] 플래그: `--dry-run`, `--verbose`, `--force`
- [ ] 진행 상황 표시

---

## 기술 스택
- **PDF 처리**: PyMuPDF (fitz)
- **DB**: SQLAlchemy 2.x + SQLite
- **파일 감시**: watchdog (Phase 2)
- **타입**: Python dataclasses, type hints

## 디렉토리 구조
```
src/
├── collectors/              # 신규 모듈
│   ├── pdf_metadata.py      # 메타데이터 추출
│   ├── pdf_extractor.py     # 텍스트 추출
│   └── orchestrator.py      # 파이프라인 조율
│
├── db/
│   └── models.py            # SourceReport 확장
│
scripts/
└── migrate_source_reports.py  # DB 마이그레이션

docs/
├── data_collection_architecture.md  # 아키텍처 설계
└── data_collection_system.md        # 사용 가이드
```

---

## 성과 요약

✅ **Phase 1 완료** (Tasks #17-21)
- PDF 메타데이터 추출기 구축
- 다중 패스 텍스트 추출 서비스
- DB 스키마 확장 (8개 컬럼 추가)
- 수집 오케스트레이터 구축
- 6개 PDF 분석 완료
- 1개 PDF 수집 테스트 성공

📊 **통계**:
- 총 PDF: 6개 (200MB)
- 분석 속도: 455페이지 → 1.2초
- DB 레코드: 19 → 20개
- 추출 품질: 평균 27-32%

🚀 **다음 작업**:
- Task #22: 파일 감시자 구축
- Task #23: CLI 명령어 구축
- 6개 PDF 전체 수집
