# 티스캐너 골프장 데이터 스크래퍼

이 프로그램은 티스캐너 웹사이트에서 골프장 예약 정보를 자동으로 수집하는 스크래핑 도구입니다.

## 기능

- 오늘부터 7일간의 골프장 예약 정보 수집
- 골프장별 티타임, 가격, 위치 등의 정보 수집
- 데이터를 엑셀 파일로 저장
- 5분 간격으로 자동 업데이트

## 필요 조건

- Python 3.7 이상
- Chrome 브라우저

## 설치 방법

1. 필요한 패키지 설치:

```bash
pip install -r requirements.txt
```
2. requirements.txt 내용:
pandas
selenium
beautifulsoup4
webdriver_manager
openpyxl
## 사용 방법

1. 프로그램 실행:
bash
python teescanner_scraping.py

2. 프로그램이 실행되면 자동으로:
   - 5분 간격으로 데이터를 수집
   - 'golf_tee_times.xlsx' 파일에 결과 저장
   - 콘솔에 진행 상황 표시

3. 프로그램 종료:
   - Ctrl+C 를 눌러 종료

## 수집 데이터

- scraping_date: 데이터 수집 시간
- play_date: 골프 라운드 날짜
- golf_course: 골프장 이름
- location: 골프장 위치
- price: 라운드 가격
- rating: 골프장 평점
- remaining_teams: 남은 팀 수
- play_time: 예약 가능한 시간대 목록

## 주의사항

- 웹사이트의 구조가 변경될 경우 코드 수정이 필요할 수 있습니다
- 과도한 요청은 피해주시기 바랍니다
- 수집된 데이터는 개인 용도로만 사용해주세요

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

이 README.md 파일은:
프로그램의 목적과 기능을 설명
설치 및 실행 방법을 단계별로 안내
수집되는 데이터 항목을 설명
필요한 의존성 패키지를 명시
사용 시 주의사항을 안내
합니다. 필요에 따라 내용을 수정하거나 보완할 수 있습니다.

