import customtkinter as ctk
from PIL import Image
import os
from datetime import datetime, timedelta
import threading
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class GolfCard(ctk.CTkFrame):
    def __init__(self, master, golf_name, location, price, teams_left, play_time="", **kwargs):
        super().__init__(master, **kwargs)
        
        # App 인스턴스를 찾아서 저장
        self.app = self.find_app_instance(master)
        
        self.configure(fg_color="#ffffff", corner_radius=10)
        
        # 골프장 이름
        self.name_label = ctk.CTkLabel(self, text=golf_name,
                                     font=ctk.CTkFont(size=16, weight="bold"),
                                     text_color="#333333")
        self.name_label.grid(row=0, column=0, padx=15, pady=(15,5), sticky="w")
        
        # 위치 정보
        self.location_label = ctk.CTkLabel(self, text=location,
                                         font=ctk.CTkFont(size=12),
                                         text_color="#666666")
        self.location_label.grid(row=1, column=0, padx=15, pady=(0,5), sticky="w")
        
        # 가격 정보
        self.price_label = ctk.CTkLabel(self, text=price,
                                      font=ctk.CTkFont(size=14),
                                      text_color="#009688")
        self.price_label.grid(row=2, column=0, padx=15, pady=(0,5), sticky="w")
        
        # 남은 팀 수
        self.teams_label = ctk.CTkLabel(self, text=f"남은 팀: {teams_left}",
                                      font=ctk.CTkFont(size=14),
                                      text_color="#666666")
        self.teams_label.grid(row=3, column=0, padx=15, pady=(0,10), sticky="w")
        
        # 알람 설정 체크박스
        self.alarm_var = ctk.BooleanVar()
        self.alarm_checkbox = ctk.CTkCheckBox(self, text="알람 설정",
                                            variable=self.alarm_var,
                                            command=self.toggle_alarm)
        self.alarm_checkbox.grid(row=4, column=0, padx=15, pady=(0,15), sticky="w")
        self.golf_name = golf_name
        self.teams_left = teams_left
        self.play_time = play_time
        self.previous_teams = teams_left

    def find_app_instance(self, widget):
        """App 인스턴스를 찾아서 반환하는 헬퍼 메서드"""
        current = widget
        while current is not None:
            if isinstance(current, App):
                return current
            current = current.master
        raise RuntimeError("App instance not found")

    def toggle_alarm(self):
        if self.alarm_var.get():
            self.app.add_alarm(self.golf_name, self.teams_left, self.play_time)
        else:
            self.app.remove_alarm(self.golf_name)

    def update_info(self, teams_left, play_time=""):
        if hasattr(self, 'previous_teams'):
            if self.alarm_var.get() and int(''.join(filter(str.isdigit, str(teams_left)))) < int(''.join(filter(str.isdigit, str(self.previous_teams)))):
                current_time = datetime.now().strftime("%H:%M:%S")
                self.app.notify_team_decrease(
                    self.golf_name,
                    self.previous_teams,
                    teams_left,
                    play_time,
                    current_time
                )
        
        self.previous_teams = self.teams_left
        self.teams_left = teams_left
        self.play_time = play_time
        self.teams_label.configure(text=f"남은 팀: {teams_left}")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("골프장 잔여팀 모니터")
        self.geometry("1200x800")
        
        self.purple_theme = {
            "primary": "#6B46C1",
            "secondary": "#9F7AEA",
            "light": "#E9D8FD",
            "bg": "#F7FAFC"
        }
        
        ctk.set_appearance_mode("light")
        self.configure(fg_color=self.purple_theme["bg"])
        
        self.scanning = False
        self.golf_cards = {}  # 골프장 카드 저장용 딕셔너리
        self.selected_date = None
        
        self.setup_layout()

        self.active_alarms = {}  # 활성화된 알람 저장
        
    def setup_layout(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.create_sidebar()
        self.create_date_tabs()  # 날짜 탭 추가
        self.create_main_content()
        self.create_alarm_area()

    def create_date_tabs(self):
        # 날짜 탭을 포함할 프레임
        self.date_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.date_frame.grid(row=0, column=1, sticky="ew", padx=20, pady=(20,0))
        
        # 현재 날짜부터 7일간의 날짜 버튼 생성
        self.date_buttons = []
        current_date = datetime.now()
        
        for i in range(8):  # 오늘 포함 8일
            date = current_date + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            formatted_date = date.strftime("%m/%d")
            
            button = ctk.CTkButton(
                self.date_frame,
                text=formatted_date,
                width=80,
                height=30,
                fg_color=self.purple_theme["secondary"] if i == 0 else "transparent",
                hover_color=self.purple_theme["light"],
                text_color="white" if i == 0 else self.purple_theme["primary"],
                command=lambda d=date_str: self.select_date(d)
            )
            button.grid(row=0, column=i, padx=5, pady=5)
            self.date_buttons.append({
                'button': button,
                'date': date_str
            })
        
        # 초기 선택 날짜 설정
        self.selected_date = current_date.strftime("%Y-%m-%d")
        
    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=self.purple_theme["primary"],
                                  corner_radius=0, width=250)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="티타임 스캐너",
                                     font=ctk.CTkFont(size=24, weight="bold"),
                                     text_color="white")
        self.logo_label.pack(pady=(30, 20))
        
        self.scan_button = ctk.CTkButton(self.sidebar, text="스캔 시작",
                                       command=self.toggle_scanning,
                                       fg_color=self.purple_theme["secondary"],
                                       hover_color=self.purple_theme["light"],
                                       text_color="white",
                                       height=40)
        self.scan_button.pack(pady=20, padx=20)
        
    def create_main_content(self):
        self.main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=1, sticky="nsew", padx=20, pady=20)
        
    def create_alarm_area(self):
        self.alarm_frame = ctk.CTkFrame(self, fg_color=self.purple_theme["light"],
                                      corner_radius=10)
        self.alarm_frame.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=20, pady=20)
        
        self.alarm_title = ctk.CTkLabel(self.alarm_frame, text="알람 현황",
                                      font=ctk.CTkFont(size=18, weight="bold"),
                                      text_color=self.purple_theme["primary"])
        self.alarm_title.pack(pady=15)
        
        # 활성 알람 요약 레이블 추가
        self.active_alarms_label = ctk.CTkLabel(self.alarm_frame,
                                                text="활성 알람: 0개",
                                                font=ctk.CTkFont(size=14),
                                                text_color=self.purple_theme["primary"])
        self.active_alarms_label.pack(pady=(0, 10))
        
        self.alarm_list = ctk.CTkTextbox(self.alarm_frame, width=300, height=600)
        self.alarm_list.pack(padx=10, pady=10, fill="both", expand=True)

    def select_date(self, date):
        self.selected_date = date
        # 버튼 스타일 업데이트
        for btn_info in self.date_buttons:
            if btn_info['date'] == date:
                btn_info['button'].configure(
                    fg_color=self.purple_theme["secondary"],
                    text_color="white"
                )
            else:
                btn_info['button'].configure(
                    fg_color="transparent",
                    text_color=self.purple_theme["primary"]
                )

    def toggle_scanning(self):
        if not self.scanning:
            if self.selected_date:
                self.scanning = True
                self.scan_button.configure(text="스캔 중지")
                self.update_alarm(f"{self.selected_date} 날짜의 스캔을 시작합니다...")
                threading.Thread(target=self.scanning_loop, daemon=True).start()
            else:
                self.update_alarm("날짜를 선택해주세요.")
        else:
            self.scanning = False
            self.scan_button.configure(text="스캔 시작")
            self.update_alarm("스캔을 중지합니다...")

    def scanning_loop(self):
        while self.scanning:
            try:
                df = self.scrape_golf_data(self.selected_date)
                if df is not None and not df.empty:
                    self.update_alarm(f"데이터 수집 완료: {len(df)}개의 골프장")
                    self.update_golf_cards(df)
                    if self.update_excel_file(df):
                        self.update_alarm("엑셀 파일 업데이트 완료")
                time.sleep(300)  # 5분 대기
            except Exception as e:
                self.update_alarm(f"오류 발생: {str(e)}")
                self.scanning = False
                self.scan_button.configure(text="스캔 시작")
                break

    def update_golf_cards(self, df):
        # 기존 카드들 제거
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.golf_cards.clear()
        
        # 새 카드 생성
        for _, row in df.iterrows():
            golf_name = row['golf_course']
            play_time = row.get('play_time', '')
            card = GolfCard(
                self.main_frame,  # master로 main_frame을 전달
                golf_name=golf_name,
                location=row['location'],
                price=row['price'],
                teams_left=row['remaining_teams'],
                play_time=play_time,
                width=250,
                height=150
            )
            card.pack(pady=10, padx=10, fill="x")
            self.golf_cards[golf_name] = card
            
            # 이전에 설정된 알람 상태 복원
            if golf_name in self.active_alarms:
                card.alarm_var.set(True)


    def update_alarm(self, message):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.alarm_list.insert("end", f"[{current_time}] {message}\n")
        self.alarm_list.see("end")

    def scrape_golf_data(self, target_date):
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
            url = f"https://www.teescanner.com/booking/list?tab=golfcourse&roundDay={target_date}"
            self.update_alarm(f"페이지 로딩 중: {url}")
            
            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'golf-inner-info'))
            )

            self.update_alarm("데이터 스크롤링 중...")
            
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
            
            data_list = []
            scraping_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for div in location_divs:
                time_element = div.find('span', class_='time')
                play_time = time_element.text.strip() if time_element else ''
                
                golf_data = {
                    'scraping_date': scraping_date,
                    'play_date': target_date,
                    'golf_course': div.find('strong').text.strip() if div.find('strong') else '정보없음',
                    'location': div.find('p', class_='location').text.strip() if div.find('p', class_='location') else '정보없음',
                    'price': div.find('span', class_='price').text.strip() if div.find('span', class_='price') else '정보없음',
                    'rating': div.find('a', class_='star-score').text.strip() if div.find('a', class_='star-score') else '정보없음',
                    'remaining_teams': div.find('button', class_='btn').text.strip() if div.find('button', class_='btn') else '정보없음',
                    'play_time': play_time
                }
                data_list.append(golf_data)

            return pd.DataFrame(data_list)
            
        except Exception as e:
            self.update_alarm(f"스크래핑 중 오류 발생: {str(e)}")
            return None
        finally:
            driver.quit()

    def update_excel_file(self, df, filename='golf_tee_times.xlsx'):
        try:
            if os.path.exists(filename):
                existing_df = pd.read_excel(filename)
                final_df = pd.concat([existing_df, df], ignore_index=True)
            else:
                final_df = df

            final_df = final_df.sort_values(['scraping_date', 'play_date'], ascending=[False, True])
            final_df = final_df.drop_duplicates()
            final_df.to_excel(filename, index=False)
            return True

        except Exception as e:
            self.update_alarm(f"파일 저장 중 오류 발생: {str(e)}")
            return False

    def add_alarm(self, golf_name, current_teams, play_time):
        # 문자열에서 숫자만 추출하여 정수로 변환
        teams_count = int(''.join(filter(str.isdigit, str(current_teams))))
        
        self.active_alarms[golf_name] = {
            'teams': teams_count,
            'play_time': play_time
        }
        message = "[알람 설정]\n"
        message += f"골프장: {golf_name}\n"
        message += f"경기 시간: {play_time}\n"
        message += f"현재 팀 수: {teams_count}팀"
        self.update_alarm(message)
        self.update_active_alarms_count()

    def remove_alarm(self, golf_name):
        if golf_name in self.active_alarms:
            message = f"❌ 알람 해제: {golf_name}"
            self.update_alarm(message)
            del self.active_alarms[golf_name]
            self.update_active_alarms_count()

    def notify_team_decrease(self, golf_name, previous_teams, current_teams, play_time, booking_time):
        prev_count = int(''.join(filter(str.isdigit, str(previous_teams))))
        curr_count = int(''.join(filter(str.isdigit, str(current_teams))))
        
        message = "[티타임 변동 알림]\n"
        message += f"골프장: {golf_name}\n"
        message += f"경기 시간: {play_time}\n"
        message += f"팀 수 변동: {prev_count}팀 → {curr_count}팀\n"
        message += f"부킹 완료 시각: {booking_time}"
        self.update_alarm(message)
        
        # 알람 소리 설정이 켜져 있는 경우 소리 재생
        if hasattr(self, 'sound_var') and self.sound_var.get():
            # 여기에 소리 재생 코드 추가 가능
            pass

    def update_active_alarms_count(self):
        count = len(self.active_alarms)
        self.active_alarms_label.configure(text=f"활성 알람: {count}개")

if __name__ == "__main__":
    app = App()
    app.mainloop()
