import re
import asyncio
import aiohttp
import os
import json
from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import User
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

API_ID = int(os.environ.get('API_ID', 2040))
API_HASH = os.environ.get('API_HASH', 'b18441a1ff607e10a989891a5462e627')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8958853008:AAEee7acztBpPWX4QN0sV4IZVwEvFxH8mBs')

user_client = TelegramClient('session', API_ID, API_HASH)
bot_app = Application.builder().token(BOT_TOKEN).build()

LEAK_SOURCES = [
    'https://raw.githubusercontent.com/Scriper1337/TelegramOSINT/main/databases/leaks.json',
    'https://raw.githubusercontent.com/Scriper1337/TelegramOSINT/main/databases/credit.json',
    'https://raw.githubusercontent.com/Scriper1337/TelegramOSINT/main/databases/social.json',
    'https://raw.githubusercontent.com/Scriper1337/TelegramOSINT/main/dumps/telegram.txt',
    'https://raw.githubusercontent.com/Scriper1337/TelegramOSINT/main/dumps/phonenumbers.txt',
    'https://raw.githubusercontent.com/Scriper1337/TelegramOSINT/main/dumps/leaked.txt'
]

async def search_all_sources(username):
    async with aiohttp.ClientSession() as session:
        for url in LEAK_SOURCES:
            try:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        if username.lower() in content.lower():
                            phone_match = re.search(r'\+\d{11,15}', content)
                            if phone_match:
                                return phone_match.group()
            except:
                pass
        # Публичные API
        api_urls = [
            f'https://api.leakcheck.net/public?query={username}',
            f'https://leak-lookup.com/api/search?key=public&query={username}',
            f'https://scylla.so/api/v1/search?q={username}',
            f'https://ghostproject.fr/api/search?username={username}',
            f'https://intelx.io/api/search?q={username}'
        ]
        for url in api_urls:
            try:
                async with session.get(url, timeout=3) as resp:
                    if resp.status == 200:
                        data = await resp.text()
                        phone_match = re.search(r'\+\d{11,15}', data)
                        if phone_match:
                            return phone_match.group()
            except:
                pass
        # Поиск по ID (если передан ID)
        if username.isdigit():
            for url in [
                f'https://api.tgstat.ru/users/{username}',
                f'https://telescan.eu/api/public/v1/user/{username}'
            ]:
                try:
                    async with session.get(url, timeout=3) as resp:
                        if resp.status == 200:
                            data = await resp.text()
                            phone_match = re.search(r'\+\d{11,15}', data)
                            if phone_match:
                                return phone_match.group()
                except:
                    pass
    return None

async def get_phone(username):
    try:
        entity = await user_client.get_entity(username)
        if not isinstance(entity, User):
            return None
        full = await user_client(GetFullUserRequest(entity))
        phone = getattr(full.full_user, 'phone', None) if hasattr(full, 'full_user') else None
        if phone:
            return phone
        phone = await search_all_sources(username)
        return phone
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Отправь @username или ID')

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_text(f'🔍 Ищу: {query}')
    phone = await get_phone(query)
    if phone:
        await update.message.reply_text(f'📱 Найден номер: {phone}')
    else:
        await update.message.reply_text('❌ Номер не найден в базах')

async def main():
    await bot_app.bot.delete_webhook(drop_pending_updates=True)
    await user_client.start()
    bot_app.add_handler(CommandHandler('start', start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
