import asyncio
import logging
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from parser import get_schedule, format_today, format_tomorrow, format_all, format_weekday, WEEKDAYS_SHORT

# ==== НАСТРОЙКИ ====
TOKEN = "8863468904:AAE25Bi-k5Fbq7bzJMey_aPP2vyRqIs7WjA" # Оставь тот токен, который у тебя был
# ====================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="⏭ Завтра")],
        [KeyboardButton(text="🗓 Вся неделя")],
        [KeyboardButton(text="Пн"), KeyboardButton(text="Вт"), KeyboardButton(text="Ср"), KeyboardButton(text="Чт"), KeyboardButton(text="Пт"), KeyboardButton(text="Сб")],
        [KeyboardButton(text="🔔 Вкл. рассылку"), KeyboardButton(text="🔕 Выкл. рассылку")],
        [KeyboardButton(text="🔄 Обновить")],
    ],
    resize_keyboard=True,
)

# --- Работа с подписчиками ---
def load_subs():
    if not os.path.exists("subscribers.txt"):
        return []
    with open("subscribers.txt", "r") as f:
        return [line.strip() for line in f if line.strip()]

def save_subs(subs):
    with open("subscribers.txt", "w") as f:
        for s in subs:
            f.write(f"{s}\n")

# --- Рассылка ---
async def send_daily_schedule():
    while True:
        now = datetime.now()
        # Ждем 6:30 утра
        if now.hour == 6 and now.minute == 30:
            subs = load_subs()
            if subs:
                try:
                    sched = get_schedule()
                    text = format_today(sched)
                    for user_id in subs:
                        try:
                            await bot.send_message(user_id, text, parse_mode="HTML")
                        except:
                            pass
                except:
                    pass
            await asyncio.sleep(60) # Ждем минуту, чтобы не отправить дважды
        await asyncio.sleep(10)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я бот с расписанием группы <b>НК9-721</b> 🎓\n\n"
        "Теперь я умею присылать расписание каждое утро в 06:30!\n"
        "Нажми <b>🔔 Вкл. рассылку</b>, чтобы подписаться.",
        reply_markup=main_kb,
        parse_mode="HTML",
    )

@dp.message(F.text == "🔔 Вкл. рассылку")
async def subscribe(message: Message):
    subs = load_subs()
    user_id = str(message.from_user.id)
    if user_id not in subs:
        subs.append(user_id)
        save_subs(subs)
        await message.answer("✅ Ты подписан на утреннюю рассылку в 06:30!")
    else:
        await message.answer("Ты уже подписан 😉")

@dp.message(F.text == "🔕 Выкл. рассылку")
async def unsubscribe(message: Message):
    subs = load_subs()
    user_id = str(message.from_user.id)
    if user_id in subs:
        subs.remove(user_id)
        save_subs(subs)
        await message.answer("❌ Рассылка отключена.")
    else:
        await message.answer("Ты и так не подписан.")

def _split(text: str, size: int = 4000):
    for i in range(0, len(text), size):
        yield text[i:i + size]

async def _send_schedule(message: Message, formatter):
    try:
        sched = get_schedule()
        text = formatter(sched)
        for chunk in _split(text):
            await message.answer(chunk, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"Ошибка: <code>{e}</code>", parse_mode="HTML")

@dp.message(F.text == "📅 Сегодня")
async def today(message: Message):
    await _send_schedule(message, format_today)

@dp.message(F.text == "⏭ Завтра")
async def tomorrow(message: Message):
    await _send_schedule(message, format_tomorrow)

@dp.message(F.text == "🗓 Вся неделя")
async def week(message: Message):
    await _send_schedule(message, format_all)

@dp.message(F.text == "🔄 Обновить")
async def refresh(message: Message):
    await message.answer("Обновляю... 🔄")
    await _send_schedule(message, format_all)

@dp.message(F.text.in_(WEEKDAYS_SHORT))
async def weekday(message: Message):
    idx = WEEKDAYS_SHORT.index(message.text)
    await _send_schedule(message, lambda s: format_weekday(s, idx))

async def main():
    # Запускаем фоновую задачу для рассылки
    asyncio.create_task(send_daily_schedule())
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
