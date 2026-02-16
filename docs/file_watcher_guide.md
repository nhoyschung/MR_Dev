# PDF File Watcher Guide

## 개요
실시간으로 디렉토리를 모니터링하여 새로운 PDF 파일을 자동으로 감지하고 수집하는 시스템입니다.

## 기능

### ✅ 실시간 파일 감지
- 새 PDF 파일 생성 이벤트 자동 감지
- 기존 PDF 파일 수정 이벤트 감지
- Debouncing으로 중복 처리 방지

### ✅ 자동 수집
- 감지된 PDF → 메타데이터 추출 → 텍스트 추출 → DB 저장
- 에러 처리 및 재시도 로직
- 중복 수집 방지 (이미 DB에 있는 파일 스킵)

### ✅ 초기 스캔
- 감시 시작 전 기존 파일 스캔
- 누락된 PDF 자동 수집

### ✅ 로깅
- 모든 이벤트 상세 로그
- 성공/실패 추적
- 런타임 통계

## 사용 방법

### 1. 기본 사용 (Python 코드)

```python
from src.collectors.watcher import watch_directory

# 디렉토리 감시 시작 (Ctrl+C로 종료)
watch_directory('user_resources/D_colect')
```

### 2. PDFWatcher 클래스 사용

```python
from src.collectors.watcher import PDFWatcher

# 초기화
watcher = PDFWatcher(
    watch_dir='user_resources/D_colect',
    debounce_seconds=2.0  # 파일 수정 후 대기 시간
)

# 감시 시작 (초기 스캔 포함)
watcher.run(
    scan_on_start=True,  # 기존 파일 스캔
    run_forever=True     # Ctrl+C까지 실행
)
```

### 3. 커스텀 콜백 사용

```python
from src.collectors.watcher import PDFWatcher

def on_ingest(report):
    """수집 완료 후 호출되는 콜백"""
    print(f"✓ Ingested: {report.filename}")
    print(f"  Pages: {report.page_count}")
    print(f"  Quality: {report.quality_score:.1%}")

watcher = PDFWatcher(
    watch_dir='user_resources/D_colect',
    on_ingest_callback=on_ingest
)

watcher.run()
```

### 4. 모듈로 직접 실행

```bash
# 기본 디렉토리 감시
python -m src.collectors.watcher

# 특정 디렉토리 감시
python -m src.collectors.watcher user_resources/incoming
```

## 동작 흐름

```
1. 감시자 시작
   ↓
2. [선택] 초기 스캔 (기존 PDF 수집)
   ↓
3. 파일 시스템 이벤트 대기
   ↓
4. PDF 파일 생성/수정 감지
   ↓
5. Debounce (2초 대기)
   ↓
6. 파일 존재 확인
   ↓
7. 수집 파이프라인 실행
   │ ├─ 메타데이터 추출
   │ ├─ 텍스트 추출
   │ └─ DB 저장
   ↓
8. 로그 출력 & 콜백 호출
   ↓
9. 다음 이벤트 대기 (3번으로)
```

## 출력 예시

```
2026-02-16 22:30:00 - root - INFO - [START] Starting PDF watcher
2026-02-16 22:30:00 - root - INFO - [WATCH] Monitoring directory: user_resources\D_colect
2026-02-16 22:30:00 - root - INFO - [WATCH] Extracted text will be saved to: user_resources\D_colect\extracted
2026-02-16 22:30:00 - root - INFO - [SCAN] Scanning for existing PDFs before starting watch...
2026-02-16 22:30:00 - root - INFO - [FOUND] 0 new PDF(s)
2026-02-16 22:30:00 - root - INFO - [SCAN] Initial scan complete: 0 ingested, 0 skipped, 0 failed
2026-02-16 22:30:00 - root - INFO - [READY] Watcher is now active. Press Ctrl+C to stop.

# 새 파일 감지
2026-02-16 22:30:15 - root - INFO - [DETECT] New PDF created: new_report.pdf
2026-02-16 22:30:17 - root - INFO - [INGEST] Starting ingestion: new_report.pdf
2026-02-16 22:30:17 - root - INFO - [METADATA] Extracting metadata: new_report.pdf
2026-02-16 22:30:17 - root - INFO - [EXTRACT] Extracting text (150 pages)...
2026-02-16 22:30:18 - root - INFO - [SUCCESS] Extraction complete:
   - Pages: 150/150
   - Text: 95,432 chars
   - Quality: 31.8%
   - Time: 0.45s
   - Files: 3
2026-02-16 22:30:18 - root - INFO - [SUCCESS] Ingested: new_report.pdf (ID: 26, Pages: 150, Quality: 31.8%)

# 이미 존재하는 파일
2026-02-16 22:30:30 - root - INFO - [DETECT] PDF modified: existing_report.pdf
2026-02-16 22:30:32 - root - INFO - [SKIP] Already ingested: existing_report.pdf

# 종료
^C2026-02-16 22:35:00 - root - INFO - [INTERRUPT] Received interrupt signal
2026-02-16 22:35:00 - root - INFO - [STOP] Stopping PDF watcher...
2026-02-16 22:35:00 - root - INFO - [STOP] Watcher stopped. Runtime: 0:05:00
```

## 설정

### Debounce 시간 조정

```python
watcher = PDFWatcher(
    watch_dir='user_resources/D_colect',
    debounce_seconds=5.0  # 5초로 증가 (대용량 파일용)
)
```

### 추출 디렉토리 변경

```python
watcher = PDFWatcher(
    watch_dir='user_resources/D_colect',
    extracted_text_dir='user_resources/extracted_texts'  # 커스텀 경로
)
```

### 초기 스캔 비활성화

```python
watcher.run(
    scan_on_start=False,  # 초기 스캔 스킵
    run_forever=True
)
```

## 상태 확인

```python
from src.collectors.watcher import PDFWatcher

watcher = PDFWatcher('user_resources/D_colect')
watcher.start()

# 상태 조회
status = watcher.get_status()

print(f"Running: {status['running']}")
print(f"Watch Dir: {status['watch_dir']}")
print(f"Runtime: {status.get('runtime_seconds', 0):.1f}s")

watcher.stop()
```

## 주의사항

### ⚠️ 대용량 파일
- 100MB 이상 파일은 debounce 시간을 늘리세요 (5-10초)
- 파일 쓰기가 완료될 때까지 대기 필요

### ⚠️ 네트워크 드라이브
- 네트워크 드라이브 감시는 이벤트 지연 발생 가능
- `scan_on_start=True` 사용 권장

### ⚠️ 리소스 사용
- 감시자는 백그라운드 스레드 사용
- 여러 디렉토리 감시 시 Observer 인스턴스 재사용 권장

### ⚠️ 중단된 수집
- Ctrl+C로 종료 시 진행 중인 수집은 완료
- 강제 종료는 피하세요 (DB 불일치 가능)

## 고급 사용

### 여러 디렉토리 감시

```python
from watchdog.observers import Observer
from src.collectors.watcher import PDFWatcherEventHandler
from src.collectors.orchestrator import IngestionOrchestrator

# 단일 Observer로 여러 디렉토리 감시
observer = Observer()

for watch_dir in ['dir1', 'dir2', 'dir3']:
    orchestrator = IngestionOrchestrator(watch_dir)
    handler = PDFWatcherEventHandler(orchestrator)
    observer.schedule(handler, watch_dir, recursive=False)

observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()

observer.join()
```

### 백그라운드 데몬

```python
import threading
from src.collectors.watcher import PDFWatcher

def run_watcher_daemon():
    """백그라운드 스레드에서 감시자 실행"""
    watcher = PDFWatcher('user_resources/D_colect')
    watcher.run(scan_on_start=True, run_forever=True)

# 데몬 스레드 시작
daemon_thread = threading.Thread(target=run_watcher_daemon, daemon=True)
daemon_thread.start()

# 메인 프로그램 계속 실행
print("Watcher running in background...")

# 종료 시 스레드도 자동 종료됨
```

## 트러블슈팅

### 파일이 감지되지 않음
1. 디렉토리 경로 확인
2. 파일 확장자 확인 (.pdf 소문자만 지원)
3. 권한 확인 (읽기/쓰기)
4. 로그 확인 (`logging.DEBUG` 레벨)

### 중복 수집
1. Debounce 시간 조정
2. DB에서 중복 확인
3. 로그에서 "[SKIP] Already ingested" 확인

### 메모리 사용량 증가
1. 대용량 PDF 처리 후 가비지 컬렉션
2. 장기 실행 시 주기적 재시작
3. 추출된 텍스트 파일 정리

## 성능

- **이벤트 감지**: <0.1초
- **Debounce 대기**: 2초 (기본값)
- **수집 시간**: PDF 크기/복잡도에 따라 0.1-2초
- **메모리 사용**: ~50-100MB (기본)
- **CPU 사용**: 수집 중 10-30%, 대기 중 <1%

## 테스트

```bash
# 단위 테스트 실행
python -m pytest tests/test_watcher.py -v

# 커버리지 포함
python -m pytest tests/test_watcher.py --cov=src.collectors.watcher
```

## 로깅 레벨 조정

```python
import logging

# DEBUG 레벨로 상세 로그 활성화
logging.basicConfig(level=logging.DEBUG)

from src.collectors.watcher import watch_directory
watch_directory('user_resources/D_colect')
```

## 참고

- watchdog 라이브러리: https://pythonhosted.org/watchdog/
- 파일 시스템 이벤트: https://docs.python.org/3/library/os.html#os.stat
- SQLAlchemy 세션 관리: https://docs.sqlalchemy.org/en/20/orm/session.html
