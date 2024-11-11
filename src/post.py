import re
import requests
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from instagrapi import Client
from src.utils import discord_webhook_log
import os
from dotenv import load_dotenv

class InstagramPostUploader:

    def __init__(self):
        load_dotenv()
        
        self.api_key = os.getenv('NEIS_API_KEY')
        self.office_code = os.getenv('OFFICE_CODE')
        self.school_code = os.getenv('SCHOOL_CODE')
        self.username = os.getenv('INSTAGRAM_USERNAME')
        self.password = os.getenv('INSTAGRAM_PASSWORD')

        self.client = Client()
        self.session_file = 'session.json'

    def get_meal_info(self):
        current_date = datetime.now().strftime("%Y%m%d")
        url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?KEY={self.api_key}&Type=xml&pIndex=1&pSize=100&ATPT_OFCDC_SC_CODE={self.office_code}&SD_SCHUL_CODE={self.school_code}&MLSV_YMD={current_date}"
        response = requests.get(url)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            meal_info = root.find('.//DDISH_NM')
            calorie_info = root.find('.//CAL_INFO')
            nutrition_info = root.find('.//NTR_INFO')
            
            if meal_info is not None and calorie_info is not None and nutrition_info is not None:
                cleaned_meal = re.sub(r'\*|\([^)]*\)', '', meal_info.text)
                menu_items = re.split(r'<br/>', cleaned_meal)
                menu_items = [item.strip() for item in menu_items if item.strip()]
                meal_text = '\n'.join(menu_items)
                calorie_text = calorie_info.text.strip()
                nutrition_text = re.sub(r'<br/>', '\n', nutrition_info.text.strip())
                
                return meal_text, calorie_text, nutrition_text
        
        discord_webhook_log("```급식 정보를 가져올 수 없습니다.```", "인스타그램 게시물 업로드")
        return None, None, None

    def create_meal_post(self):
        meal_text, calorie_text, nutrition_text = self.get_meal_info()
        
        if meal_text is None:
            print("급식 정보를 가져올 수 없어 이미지를 생성하지 않았습니다.")
            return False
        
        background = Image.open("assets/bg-post.jpg")
        draw = ImageDraw.Draw(background)
        
        title_font = ImageFont.truetype("assets/Pretendard-ExtraBold.otf", 96)
        content_font = ImageFont.truetype("assets/Pretendard-Medium.otf", 85)
        day_font = ImageFont.truetype("assets/Pretendard-ExtraBold.otf", 170)
        
        current_date = datetime.now()
        date_string = current_date.strftime("%m월 %d일")
        weekday = ["월", "화", "수", "목", "금", "토", "일"][current_date.weekday()]
        
        draw.text((60, 60), f"{date_string} 급식", font=title_font, fill=(0, 0, 0))
        draw.text((827, 10), weekday, font=day_font, fill=(255, 255, 255))
        
        line_spacing = int(content_font.size * 0.25)
        
        draw.multiline_text((60, 175), meal_text, font=content_font, fill=(0, 0, 0), spacing=line_spacing)
        
        background.save("meal-post.jpg")
        print("급식 정보 이미지가 생성되었습니다.")
        return True

    def upload_post(self):
        meal_text, calorie_text, nutrition_text = self.get_meal_info()
        
        if meal_text is None:
            print("급식 정보를 가져올 수 없어 인스타그램에 포스팅하지 않았습니다.")
            return
        
        if not self.create_meal_post():
            return
        
        try:
            # 세션을 파일에서 로드
            if os.path.exists(self.session_file):
                self.client.load_settings(self.session_file)
            else:
                # 로그인 및 세션 저장
                self.client.login(self.username, self.password)
                self.client.dump_settings(self.session_file)
            
            caption = (
                f"{datetime.now().strftime('%Y년 %m월 %d일')} 급식 메뉴 입니다!\n\n"
                f"{meal_text}\n\n"
                f"총 칼로리 량: {calorie_text}\n\n"
                f"칼로리 정보:\n{nutrition_text}"
            )
            
            self.client.photo_upload("meal-post.jpg", caption)
            
            discord_webhook_log(f"```성공적으로 인스타그램 게시물을 업로드했습니다!```", "게시물 업로드 완료")
            print("인스타그램에 급식 정보를 성공적으로 포스팅했습니다.")
        
        except Exception as e:
            discord_webhook_log(f"```{e}```", "게시물 업로드 중 오류가 발생했습니다.")
            print(f"인스타그램 포스팅 중 오류가 발생했습니다: {str(e)}")