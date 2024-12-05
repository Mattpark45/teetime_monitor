import time
import pandas as pd
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def scrape_golf_data():
    """티스캐너의 모든 골프장 데이터를 스크래핑"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    try:
        # 현재 날짜부터 7일간의 데이터를 수집
        data_list = []
        scraping_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_date = datetime.now()

        # 오늘부터 7일 후까지 순회
        for day_offset in range(8):  # 0부터 7까지 (총 8일)
            target_date = current_date + timedelta(days=day_offset)
            formatted_date = target_date.strftime("%Y-%m-%d")
            url = f"https://www.teescanner.com/booking/list?tab=golfcourse&roundDay={formatted_date}"
            
            print(f"스크래핑 시작: {url}")
            driver.get(url)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'golf-inner-info'))
            )

            # 무한 스크롤
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            location_divs = soup.find_all('div', class_='golf-inner-info')

            for div in location_divs:
                # 시간 정보 수집
                time_spans = div.find_all('span', class_='time')
                play_times = [span.text.strip() for span in time_spans] if time_spans else []
                
                golf_data = {
                    'scraping_date': scraping_date,
                    'play_date': formatted_date,
                    'golf_course': div.find('strong').text.strip() if div.find('strong') else '정보없음',
                    'location': div.find('p', class_='location').text.strip() if div.find('p', class_='location') else '정보없음',
                    'price': div.find('span', class_='price').text.strip() if div.find('span', class_='price') else '정보없음',
                    'rating': div.find('a', class_='star-score').text.strip() if div.find('a', class_='star-score') else '정보없음',
                    'remaining_teams': div.find('button', class_='btn').text.strip() if div.find('button', class_='btn') else '정보없음',
                    'play_time': play_times
                }
                data_list.append(golf_data)

            time.sleep(1)  # 각 날짜별 요청 사이에 짧은 대기 시간 추가

        return pd.DataFrame(data_list)

    except Exception as e:
        print(f"스크래핑 중 오류 발생: {str(e)}")
        return None
    finally:
        driver.quit()

def update_excel_file(df, filename='golf_tee_times.xlsx'):
    """데이터프레임을 엑셀 파일로 저장/업데이트하며 중복 데이터 제거"""
    try:
        # 새로운 데이터프레임의 날짜 형식 통일
        df['scraping_date'] = pd.to_datetime(df['scraping_date'])
        df['play_date'] = pd.to_datetime(df['play_date'])

        if os.path.exists(filename):
            # 기존 파일 읽기
            existing_df = pd.read_excel(filename)
            # 기존 데이터프레임의 날짜 형식 통일
            existing_df['scraping_date'] = pd.to_datetime(existing_df['scraping_date'])
            existing_df['play_date'] = pd.to_datetime(existing_df['play_date'])
            
            # 데이터 병합
            final_df = pd.concat([existing_df, df], ignore_index=True)
        else:
            final_df = df

        # 중복 제거 로직
        # 골프장과 플레이 날짜가 같은 경우 가장 최근에 스크래핑된 데이터만 유지
        final_df = final_df.sort_values('scraping_date', ascending=False)
        final_df = final_df.drop_duplicates(
            subset=['golf_course', 'play_date'], 
            keep='first'
        )

        # 최종 정렬: 스크래핑 날짜 내림차순, 플레이 날짜 오름차순
        final_df = final_df.sort_values(
            ['scraping_date', 'play_date'], 
            ascending=[False, True]
        )

        # 날짜 형식을 문자열로 변환하여 저장
        final_df['scraping_date'] = final_df['scraping_date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        final_df['play_date'] = final_df['play_date'].dt.strftime('%Y-%m-%d')

        # 엑셀 파일로 저장
        final_df.to_excel(filename, index=False)
        
        print(f"데이터 저장 완료: {filename}")
        print(f"총 레코드 수: {len(final_df)}")
        print(f"유니크 골프장 수: {final_df['golf_course'].nunique()}")
        print(f"날짜 범위: {final_df['play_date'].min()} ~ {final_df['play_date'].max()}")
        
        return True

    except Exception as e:
        print(f"파일 저장 중 오류 발생: {str(e)}")
        return False


def main():
    while True:
        try:
            print("\n데이터 수집 시작")
            
            df = scrape_golf_data()
            if df is not None and not df.empty:
                print(f"수집된 데이터 수: {len(df)}")
                if update_excel_file(df):
                    print("데이터 업데이트 성공")
                else:
                    print("데이터 업데이트 실패")
            else:
                print("수집된 데이터가 없습니다")

            print("\n다음 업데이트까지 300초 대기")
            time.sleep(300)

        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"예상치 못한 오류 발생: {str(e)}")
            time.sleep(60)

if __name__ == "__main__":
    main()
