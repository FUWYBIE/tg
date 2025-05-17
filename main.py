import logging
import os
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from apscheduler.schedulers.blocking import BlockingScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

POST_TIMES = ["10:00", "13:00", "15:00", "17:00", "21:00"]
BASE_URL = "https://www.playground.ru/news"

def get_news():
    try:
        response = requests.get(BASE_URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.select("div.article-preview")
        news_list = []

        for article in articles[:10]:
            title_tag = article.select_one(".article-preview-title")
            link_tag = title_tag.find("a") if title_tag else None
            title = title_tag.text.strip() if title_tag else ""
            link = link_tag["href"] if link_tag else ""
            image_tag = article.select_one("img")
            image = image_tag["src"] if image_tag else ""

            if link and not link.startswith("http"):
                link = "https://www.playground.ru" + link
            if image and not image.startswith("http"):
                image = "https://www.playground.ru" + image

            if title and link:
                news_list.append({"title": title, "link": link, "image": image})

        return news_list
    except Exception as e:
        logger.error(f"Ошибка при получении новостей: {e}")
        return []

def post_news():
    news_items = get_news()
    if not news_items:
        logger.warning("Нет новостей для публикации")
        return

    post = random.choice(news_items)
    caption = f"<b>{post['title']}</b>\n\n<a href=\"{post['link']}\">Читать на Playground</a>"

    try:
        if post["image"]:
            bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=post["image"], caption=caption, parse_mode="HTML")
        else:
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=caption, parse_mode="HTML")
        logger.info(f"Опубликована новость: {post['title']}")
    except TelegramError as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")

scheduler = BlockingScheduler()

for time_str in POST_TIMES:
    hour, minute = map(int, time_str.split(":"))
    scheduler.add_job(post_news, "cron", hour=hour, minute=minute)

if __name__ == "__main__":
    logger.info("Бот запущен")
    scheduler.start()
