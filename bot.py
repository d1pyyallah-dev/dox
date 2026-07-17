import re
import asyncio
import aiohttp
import os
from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import User
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
BOT_TOKEN = '8958853008:AAEee7acztBpPWX4QN0sV4IZVwEvFxH8mBs'

user_client = TelegramClient('session', API_ID, API_HASH)
bot_app = Application.builder().token(BOT_TOKEN).build()

async def get_phone(username):
    try:
        entity = await user_client.get_entity(username)
        if not isinstance(entity, User):
            return None
        full = await user_client(GetFullUserRequest(entity))
        phone = getattr(full.full_user, 'phone', None) if hasattr(full, 'full_user') else None
        if phone:
            return phone
        async with aiohttp.ClientSession() as session:
            for url in [
                f'https://api.leakcheck.net/public?query={username}',
                f'https://leak-lookup.com/api/search?key=public&query={username}'
            ]:
                try:
                    async with session.get(url, timeout=3) as resp:
                        if resp.status == 200:
                            data = await resp.text()
                            match = re.search(r'\+\d{11,15}', data)
                            if match:
                                return match.group()
                except:
                    pass
        return None
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Send @username or ID')

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_text(f'Searching: {query}')
    phone = await get_phone(query)
    if phone:
        await update.message.reply_text(f'📱 {phone}')
    else:
        await update.message.reply_text('❌ Not found')

async def main():
    await bot_app.bot.delete_webhook(drop_pending_updates=True)
    try:
        await user_client.start()
    except:
        if os.path.exists('session.session'):
            os.remove('session.session')
        await user_client.start()
    bot_app.add_handler(CommandHandler('start', start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
