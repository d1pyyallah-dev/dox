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

leak_sources = [
    'https://raw.githubusercontent.com/Scriper1337/TelegramOSINT/main/databases/leaks.json',
    'https://raw.githubusercontent.com/Scriper1337/TelegramOSINT/main/databases/credit.json',
    'https://raw.githubusercontent.com/Scriper1337/TelegramOSINT/main/databases/social.json'
]

async def load_leaks():
    all_data = []
    async with aiohttp.ClientSession() as session:
        for url in leak_sources:
            try:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, list):
                            all_data.extend(data)
                        elif isinstance(data, dict):
                            all_data.append(data)
            except:
                pass
    return all_data

async def search_in_leaks(query, leaks):
    results = []
    query_lower = query.lower()
    for entry in leaks:
        entry_str = json.dumps(entry).lower()
        if query_lower in entry_str:
            results.append(entry)
            if 'phone' in entry_str:
                phone_match = re.search(r'\+\d{11,15}', entry_str)
                if phone_match:
                    return phone_match.group()
    return None

async def search_breachcompilation(username):
    async with aiohttp.ClientSession() as session:
        urls = [
            f'https://api.leakcheck.net/public?query={username}',
            f'https://leak-lookup.com/api/search?key=public&query={username}',
            f'https://scylla.so/api/v1/search?q={username}',
            f'https://ghostproject.fr/api/search?username={username}',
            f'https://intelx.io/api/search?q={username}'
        ]
        for url in urls:
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

async def search_public_dumps(username):
    async with aiohttp.ClientSession() as session:
        dumps = [
            'https://raw.githubusercontent.com/Scriper1337/TelegramOSINT/main/dumps/telegram.txt',
            'https://raw.githubusercontent.com/Scriper1337/TelegramOSINT/main/dumps/phonenumbers.txt',
            'https://raw.githubusercontent.com/Scriper1337/TelegramOSINT/main/dumps/leaked.txt'
        ]
        for dump_url in dumps:
            try:
                async with session.get(dump_url, timeout=5) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        lines = content.split('\n')
                        for line in lines:
                            if username.lower() in line.lower():
                                phone_match = re.search(r'\+\d{11,15}', line)
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
        leaks = await load_leaks()
        phone = await search_in_leaks(username, leaks)
        if phone:
            return phone
        phone = await search_breachcompilation(username)
        if phone:
            return phone
        phone = await search_public_dumps(username)
        if phone:
            return phone
        return None
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
    await user_client.start()
    bot_app.add_handler(CommandHandler('start', start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
