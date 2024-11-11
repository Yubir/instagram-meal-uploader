import requests
from instagrapi import Client
from xml.etree import ElementTree
import re
from PIL import Image, ImageDraw, ImageFont
import datetime
from src.utils import discord_webhook_log
import os
from dotenv import load_dotenv

class InstagramStoryUploader:
    def __init__(self):
        self.before_storyid = None
        load_dotenv()
        
        self.api_key = os.getenv('NEIS_API_KEY')
        self.office_code = os.getenv('OFFICE_CODE')
        self.school_code = os.getenv('SCHOOL_CODE')
        self.username = os.getenv('INSTAGRAM_USERNAME')
        self.password = os.getenv('INSTAGRAM_PASSWORD')
        self.session_file = 'session.json'

    def get_meal_info(self):
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        # current_date = '20240706'
        url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?KEY={self.api_key}&Type=xml&pIndex=1&pSize=100&ATPT_OFCDC_SC_CODE={self.office_code}&SD_SCHUL_CODE={self.school_code}&MLSV_YMD={current_date}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            discord_webhook_log(f"```Error: {response.status_code}```", "Error")
            return None

        root = ElementTree.fromstring(response.content)
        result_code = root.find('.//RESULT/CODE')
        if result_code is not None and result_code.text == 'INFO-200':
            print("INFO-200: 급식 정보가 없습니다. 내일 다시 시도합니다.")
            discord_webhook_log("```INFO-200: 급식 정보가 없습니다. 내일 다시 시도합니다.```", "Info")
            return None

        meal_info_text = ''
        for meal in root.iter('row'):
            dish_name = meal.find('DDISH_NM')
            if dish_name is not None:
                cleaned_dish = re.sub(r'\*|\(\d.*?\)', '', dish_name.text).strip()
                meal_info_text += cleaned_dish.replace('<br/>', '\n') + '\n'

        return meal_info_text.strip()

    def create_meal_image(self, meal_info_text):
        lines = meal_info_text.split('\n')
        background_image_path = 'assets/bg-story.jpg'
        img = Image.open(background_image_path)
        d = ImageDraw.Draw(img)
        font = ImageFont.truetype("assets/Pretendard-ExtraBold.otf", 100)

        x, y = 150, 620
        line_height = 110
        shadowcolor = 'black'
        outline_thickness = 6

        for line in lines:
            for dx in range(-outline_thickness, outline_thickness+1):
                for dy in range(-outline_thickness, outline_thickness+1):
                    if dx != 0 or dy != 0:
                        d.text((x+dx, y+dy), line, font=font, fill=shadowcolor)
            d.text((x, y), line, fill='white', font=font)
            y += line_height

        img.save('meal-story.jpg')

    def upload_story(self):
        meal_info = self.get_meal_info()
        if not meal_info:
            return

        self.create_meal_image(meal_info)

        cl = Client()

        # 세션을 파일에서 로드
        if os.path.exists(self.session_file):
            cl.load_settings(self.session_file)
        else:
            # 로그인 및 세션 저장
            cl.login(self.username, self.password)
            cl.dump_settings(self.session_file)

        try:
            story = cl.photo_upload_to_story('meal-story.jpg')
            print(f'급식 정보가 인스타그램 스토리에 업로드되었습니다. 스토리 ID: {story.pk}')
            discord_webhook_log(f'```급식 정보가 인스타그램 스토리에 업로드되었습니다.\n스토리 ID: {story.pk}\n급식 정보: \n{meal_info}```', '급식 정보 업로드 완료')
            self.before_storyid = story.pk
        except Exception as e:
            print(f"An error occurred: {e}")
            discord_webhook_log(f"```An error occurred: {e}```", "Error")

    def delete_previous_story(self):
        if self.before_storyid is None:
            return

        cl = Client()
        
        # 세션을 파일에서 로드
        if os.path.exists(self.session_file):
            cl.load_settings(self.session_file)
        else:
            # 로그인 및 세션 저장
            cl.login(self.username, self.password)
            cl.dump_settings(self.session_file)

        try:
            cl.story_delete(self.before_storyid)
            print(f"이전 급식 정보가 제거되었습니다. 스토리 ID: {self.before_storyid}")
            discord_webhook_log(f"```이전 급식 정보가 제거되었습니다.\n스토리 ID: {self.before_storyid}```", "이전 급식 정보 제거 완료")
            self.before_storyid = None
        except Exception as e:
            print(f"스토리를 삭제하는데 오류가 발생했습니다: {e}")
            discord_webhook_log(f"```스토리를 삭제하는데 오류가 발생했습니다: {e}```", "Error")