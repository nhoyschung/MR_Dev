# CLI Commands Guide

## 개요
PDF 데이터 수집 시스템을 위한 명령줄 인터페이스(CLI) 도구 모음입니다.

## 설치된 명령어

1. **status** - 수집 상태 및 통계 확인
2. **scan_folder** - 폴더 스캔 & 일괄 수집
3. **ingest_pdf** - 단일 PDF 수집
4. **watch** - 실시간 파일 감시자 시작

---

## 1. status - 수집 상태 확인

### 기본 사용
```bash
python -m src.collectors.cli_status
```

### 옵션
- `--detailed` - 수집된 PDF 전체 목록 표시
- `--stats` - 상세 통계 표시
- `--all` - 모든 정보 표시 (detailed + stats)
- `--watch-dir <path>` - 감시 디렉토리 지정 (기본값: user_resources/D_colect)

### 예제
```bash
# 기본 상태
python -m src.collectors.cli_status

# 상세 목록 포함
python -m src.collectors.cli_status --detailed

# 통계 표시
python -m src.collectors.cli_status --stats

# 모든 정보
python -m src.collectors.cli_status --all
```

### 출력 예시
```
================================================================================
                              PDF INGESTION STATUS
================================================================================

Overview
┌──────────────────────────────────────────────────────────────────────────┐
│ Total Reports in DB: 25                                                  │
│ PDF Files Tracked  : 6                                                   │
│ PDFs in Directory  : 6 (user_resources\D_colect)                         │
│ Unprocessed        : 0                                                   │
│ Status: extracted  : 6                                                   │
│ Status: ingested   : 19                                                  │
└──────────────────────────────────────────────────────────────────────────┘

Statistics
----------

PDF Statistics
┌──────────────────────────────────────────────────────────────────────────┐
│ Total Size           : 200.6 MB                                          │
│ Avg Size             : 33.4 MB                                           │
│ Total Pages          : 1,165                                             │
│ Avg Quality          : 33.7%                                             │
│ Total Extraction Time: 2.6s                                              │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. scan_folder - 폴더 스캔 & 일괄 수집

### 기본 사용
```bash
python -m src.collectors.cli_scan_folder [directory]
```

### 인자
- `directory` - 스캔할 디렉토리 (기본값: user_resources/D_colect)

### 옵션
- `--dry-run` - 실제 수집 없이 대상 확인만
- `--force` - 이미 수집된 파일도 재처리
- `-v, --verbose` - 상세 출력
- `--output-dir <path>` - 추출 텍스트 저장 디렉토리

### 예제
```bash
# 기본 디렉토리 스캔
python -m src.collectors.cli_scan_folder

# 특정 디렉토리 스캔
python -m src.collectors.cli_scan_folder /path/to/pdfs

# Dry run (수집 안 함)
python -m src.collectors.cli_scan_folder --dry-run

# 강제 재처리
python -m src.collectors.cli_scan_folder --force

# 상세 출력
python -m src.collectors.cli_scan_folder -v
```

### 출력 예시
```
================================================================================
                          PDF FOLDER SCAN & INGEST
================================================================================

ℹ Directory: D:\AI_Projects\MR-system\user_resources\D_colect

Scanning for PDFs
-----------------
ℹ Found 3 new PDF(s):
  • report1.pdf
  • report2.pdf
  • report3.pdf

Ingest 3 PDF(s)? [Y/n]: y

Ingesting PDFs
--------------
[██████████████████████████████████████████████████] 100% (3/3) - Complete

Summary
-------

Ingestion Results
┌──────────────────────────────────────────────────────────────────────────┐
│ Total PDFs           : 3                                                 │
│ Successfully Ingested: 3 (green)                                         │
│ Skipped              : 0 (yellow)                                        │
│ Failed               : 0 (red)                                           │
│ Total Pages          : 450                                               │
│ Total Size           : 85.2 MB                                           │
│ Total Time           : 1.5s                                              │
│ Avg Quality          : 35.2%                                             │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. ingest_pdf - 단일 PDF 수집

### 기본 사용
```bash
python -m src.collectors.cli_ingest_pdf <pdf_file>
```

### 인자
- `pdf_file` - 수집할 PDF 파일 경로 (필수)

### 옵션
- `--force` - 이미 수집된 파일 재처리
- `-v, --verbose` - 상세 출력
- `--output-dir <path>` - 추출 텍스트 저장 디렉토리

### 예제
```bash
# PDF 수집
python -m src.collectors.cli_ingest_pdf report.pdf

# 강제 재처리
python -m src.collectors.cli_ingest_pdf report.pdf --force

# 커스텀 출력 디렉토리
python -m src.collectors.cli_ingest_pdf report.pdf --output-dir /path/to/extracted

# 상세 출력
python -m src.collectors.cli_ingest_pdf report.pdf -v
```

### 출력 예시
```
================================================================================
                                PDF INGESTION
================================================================================

ℹ File: Market_Analysis_2025.pdf
ℹ Path: D:\AI_Projects\MR-system\user_resources\D_colect\Market_Analysis_2025.pdf

Extracting Metadata
-------------------
  Filename: Market_Analysis_2025.pdf
  Size: 45.3 MB
  Pages: 250
  Report Type: market_analysis
  City: Hanoi
  Period: 2025-H2

Proceed with ingestion? [Y/n]: y

Ingesting PDF
-------------
✓ Ingested successfully!

Ingestion Results
┌──────────────────────────────────────────────────────────────────────────┐
│ Report ID        : 26                                                    │
│ Filename         : Market_Analysis_2025.pdf                              │
│ Report Type      : market_analysis                                       │
│ Pages            : 250                                                   │
│ Size             : 45.3 MB                                               │
│ Status           : extracted                                             │
│ Extraction Time  : 650ms                                                 │
│ Quality Score    : 28.5%                                                 │
│ Text Length      : 145,230 chars                                         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. watch - 실시간 파일 감시자

### 기본 사용
```bash
python -m src.collectors.cli_watch [directory]
```

### 인자
- `directory` - 감시할 디렉토리 (기본값: user_resources/D_colect)

### 옵션
- `--no-scan` - 초기 스캔 생략
- `--debounce <seconds>` - Debounce 시간 (기본값: 2.0)
- `--output-dir <path>` - 추출 텍스트 저장 디렉토리

### 예제
```bash
# 기본 디렉토리 감시
python -m src.collectors.cli_watch

# 특정 디렉토리 감시
python -m src.collectors.cli_watch /path/to/pdfs

# 초기 스캔 없이
python -m src.collectors.cli_watch --no-scan

# Debounce 시간 조정 (대용량 파일용)
python -m src.collectors.cli_watch --debounce 5.0

# 커스텀 출력 디렉토리
python -m src.collectors.cli_watch --output-dir /path/to/extracted
```

### 출력 예시
```
================================================================================
                               PDF FILE WATCHER
================================================================================

ℹ Watch Directory: D:\AI_Projects\MR-system\user_resources\D_colect
ℹ Debounce: 2.0s
ℹ Initial Scan: Yes

ℹ Press Ctrl+C to stop

2026-02-16 23:00:00 - root - INFO - [START] Starting PDF watcher
2026-02-16 23:00:00 - root - INFO - [WATCH] Monitoring directory: user_resources\D_colect
2026-02-16 23:00:00 - root - INFO - [SCAN] Scanning for existing PDFs before starting watch...
2026-02-16 23:00:00 - root - INFO - [FOUND] 0 new PDF(s)
2026-02-16 23:00:00 - root - INFO - [READY] Watcher is now active. Press Ctrl+C to stop.

# 새 파일 감지 시
2026-02-16 23:05:15 - root - INFO - [DETECT] New PDF created: new_report.pdf
2026-02-16 23:05:17 - root - INFO - [INGEST] Starting ingestion: new_report.pdf
2026-02-16 23:05:17 - root - INFO - [METADATA] Extracting metadata: new_report.pdf
2026-02-16 23:05:17 - root - INFO - [EXTRACT] Extracting text (150 pages)...
2026-02-16 23:05:18 - root - INFO - [SUCCESS] Extraction complete:
   - Pages: 150/150
   - Text: 95,432 chars
   - Quality: 31.8%
   - Time: 0.45s
   - Files: 3
2026-02-16 23:05:18 - root - INFO - [SUCCESS] Ingested: new_report.pdf (ID: 26, Pages: 150, Quality: 31.8%)

# 종료
^C
2026-02-16 23:10:00 - root - INFO - [INTERRUPT] Received interrupt signal
ℹ Watcher stopped by user
```

---

## 공통 기능

### 색상 출력
- ✓ 초록색 - 성공 메시지
- ✗ 빨간색 - 에러 메시지
- ⚠ 노란색 - 경고 메시지
- ℹ 파란색 - 정보 메시지

### 진행 상태 표시
- 프로그레스 바: `[████████░░] 80% (4/5)`
- 실시간 업데이트
- 현재 처리 중인 파일 표시

### 대화형 확인
- 중요한 작업 전 사용자 확인 요청
- `[Y/n]` 형식 (대문자가 기본값)
- Enter 키로 기본값 선택

---

## 일반적인 워크플로우

### 1. 초기 설정 후 모든 파일 수집
```bash
# 상태 확인
python -m src.collectors.cli_status

# 폴더 스캔 & 수집
python -m src.collectors.cli_scan_folder

# 결과 확인
python -m src.collectors.cli_status --stats
```

### 2. 단일 파일 수집
```bash
# 새 PDF 수집
python -m src.collectors.cli_ingest_pdf new_report.pdf

# 상태 확인
python -m src.collectors.cli_status --detailed
```

### 3. 자동화 설정
```bash
# 감시자 시작 (백그라운드 실행 권장)
python -m src.collectors.cli_watch

# 또는 nohup으로 백그라운드 실행 (Linux/Mac)
nohup python -m src.collectors.cli_watch > watcher.log 2>&1 &
```

### 4. 정기 점검
```bash
# 전체 통계 확인
python -m src.collectors.cli_status --all

# 누락된 파일 확인 & 수집
python -m src.collectors.cli_scan_folder
```

---

## 트러블슈팅

### 명령어를 찾을 수 없음
```bash
# 올바른 형식 사용
python -m src.collectors.cli_status  # ✓ 올바름
python cli_status.py                 # ✗ 잘못됨
```

### 권한 에러
```bash
# Windows: 관리자 권한으로 실행
# Linux/Mac: sudo 사용 또는 디렉토리 권한 확인
chmod 755 /path/to/pdfs
```

### 인코딩 에러 (한글 파일명)
```bash
# Windows: UTF-8 인코딩 설정
chcp 65001

# 또는 환경 변수 설정
set PYTHONIOENCODING=utf-8
```

### 색상이 표시되지 않음
- Windows: ANSI 색상 지원 확인
- 또는 색상 없는 환경변수 설정: `NO_COLOR=1`

---

## 스크립트 통합

### Bash 스크립트 예제
```bash
#!/bin/bash
# daily_sync.sh - 일일 PDF 동기화

# 로그 디렉토리 생성
mkdir -p logs

# 날짜
DATE=$(date +%Y%m%d)

# 상태 확인
echo "[$DATE] Checking status..."
python -m src.collectors.cli_status > logs/status_$DATE.txt

# 새 파일 스캔 & 수집
echo "[$DATE] Scanning for new files..."
python -m src.collectors.cli_scan_folder >> logs/sync_$DATE.log 2>&1

# 완료
echo "[$DATE] Sync complete"
```

### Windows 배치 파일 예제
```batch
@echo off
REM daily_sync.bat - 일일 PDF 동기화

REM 로그 디렉토리 생성
if not exist logs mkdir logs

REM 날짜
set DATE=%date:~0,4%%date:~5,2%%date:~8,2%

REM 상태 확인
echo [%DATE%] Checking status...
python -m src.collectors.cli_status > logs\status_%DATE%.txt

REM 새 파일 스캔 & 수집
echo [%DATE%] Scanning for new files...
python -m src.collectors.cli_scan_folder >> logs\sync_%DATE%.log 2>&1

REM 완료
echo [%DATE%] Sync complete
```

### Python 스크립트 예제
```python
#!/usr/bin/env python
"""custom_workflow.py - 커스텀 수집 워크플로우"""

import subprocess
import sys

def run_command(cmd):
    """명령어 실행"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout

# 상태 확인
print("Checking status...")
status = run_command("python -m src.collectors.cli_status")
print(status)

# 새 파일 수집
print("\nScanning for new files...")
scan = run_command("python -m src.collectors.cli_scan_folder --dry-run")
print(scan)

# 사용자 확인 후 실제 수집
response = input("Proceed with ingestion? [Y/n]: ")
if response.lower() in ['', 'y', 'yes']:
    run_command("python -m src.collectors.cli_scan_folder")
    print("Ingestion complete!")
```

---

## 참고

- **전체 문서**: `docs/data_collection_system.md`
- **파일 감시자 가이드**: `docs/file_watcher_guide.md`
- **아키텍처 설계**: `docs/data_collection_architecture.md`
- **소스 코드**: `src/collectors/`
