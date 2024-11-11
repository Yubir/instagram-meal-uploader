import schedule
import time
from src.story import InstagramStoryUploader
from src.post import InstagramPostUploader

print("실행되었습니다.")

story_uploader = InstagramStoryUploader()
post_uploader = InstagramPostUploader()

schedule.every().day.at("07:00").do(story_uploader.upload_story)
schedule.every().day.at("20:00").do(story_uploader.delete_previous_story)
schedule.every().day.at("06:00").do(post_uploader.upload_post)

# story_uploader.upload_story() # debug
# post_uploader.upload_post() # debug

while True:
    schedule.run_pending()
    time.sleep(1)