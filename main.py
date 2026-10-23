import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from parser import (
    get_schedule,
    format_today,
    format_tomorrow,
    format_all,
    format_weekday,
    WEEKDAYS_SHORT,
)

# ==== НАСТРОЙКИ ====
TOKEN = "8863468904:AAEdjoFJCPBAQLH6UkdjrA5W5DjbrlEZomc"
# ====================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Меню
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="⏭ Завтра")],
        [KeyboardButton(text="🗓 Вся неделя")],
        [
            KeyboardButton(text="Пн"), KeyboardButton(text="Вт"),
            KeyboardButton(text="Ср"), KeyboardButton(text="Чт"),
            KeyboardButton(text="Пт"), KeyboardButton(text="Сб"),
        ],
        [KeyboardButton(text="🔄 Обновить")],
    ],
    resize_keyboard=True,
)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот с расписанием группы <b>НК9-721</b> 🤍\n"
        "\n"
        "Что я умею:\n"
        "‧₊˚ <b>Сегодня</b> — пары на сегодня\n"
        "₊˚ <b>Завтра</b> — пары на завтра\n"
        "✩ <b>Вся неделя</b> — всё расписание целиком\n"
        "⊹♡ <b>Пн–Сб</b> — расписание на конкретный день недели\n"
        "🔄 <b>Обновить</b> — заново загрузить расписание с сайта\n"
        "\n"
        "Данные беру с edu.tgpi.ru \n"
        "Если что-то не работает — напиши @llzok",
        reply_markup=main_kb,
        parse_mode="HTML",
    )


def _split(text: str, size: int = 4000):
    for i in range(0, len(text), size):
        yield text[i:i + size]


async def _send_schedule(message: Message, formatter):
    """Универсальная отправка расписания."""
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
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
