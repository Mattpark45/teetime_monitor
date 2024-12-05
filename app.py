from flask import Flask, render_template, jsonify
import pandas as pd
from scraper import scrape_golf_data, update_excel_file
import threading
import time

app = Flask(__name__)

# 전역 변수로 최신 데이터 저장
latest_data = None
last_update = None

def background_scraping():
    global latest_data, last_update
    while True:
        try:
            print("\n데이터 수집 시작")
            df = scrape_golf_data()
            if df is not None and not df.empty:
                latest_data = df
                last_update = time.strftime("%Y-%m-%d %H:%M:%S")
                update_excel_file(df)
            time.sleep(300)  # 5분 대기
        except Exception as e:
            print(f"스크래핑 오류: {str(e)}")
            time.sleep(60)

@app.route('/')
def home():
    return render_template('index.html', last_update=last_update)

@app.route('/api/golf-data')
def get_golf_data():
    if latest_data is not None:
        return jsonify(latest_data.to_dict('records'))
    return jsonify([])

if __name__ == '__main__':
    # 스크래핑 스레드 시작
    scraper_thread = threading.Thread(target=background_scraping, daemon=True)
    scraper_thread.start()
    
    # Flask 앱 실행
    app.run(host='0.0.0.0', port=5000) 