import re
import json
import requests
from datetime import date

URL = "https://edu.tgpi.ru/schedule/group/13887/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}

LESSON_TIMES = {
    1: "08:30–10:05",
    2: "10:15–11:50",
    3: "12:10–13:45",
    4: "14:00–15:35",
    5: "15:45–17:20",
    6: "17:30–19:05",
    7: "19:15–20:50",
}

WEEKDAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

# Короткие названия для кнопок
WEEKDAYS_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# Типы занятий: цифра -> (короткое обозначение, эмодзи)
# Пока знаем только 1=лек, 2=пр. Остальные допишем, когда увидим в реальном расписании.
TYPE_MAP = {
    1: ("лек", "📘"),
    2: ("пр",  "📝"),
}


def get_schedule():
    """Возвращает dict: {'gname': 'НК9-721', 'days': [ {...}, {...} ]}"""
    r = requests.get(URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    html = r.text

    m = re.search(r"var\s+preload\s*=\s*(\{.*?\});", html, re.DOTALL)
    if not m:
        raise RuntimeError("Не нашёл preload в HTML")

    data = json.loads(m.group(1))
    return data["schedule"]


def _format_lesson(rec):
    """Форматирует одну пару."""
    subject = rec["subject"]
    aud = rec.get("aud", "")
    ltype = rec.get("type", 0)
    teachers = ", ".join(t["teacher"] for t in rec.get("teacher", []))
    lessons = rec.get("lesson", [])
    lesson_num = lessons[0] if lessons else 0
    time_str = LESSON_TIMES.get(lesson_num, "")

    short, emoji = TYPE_MAP.get(ltype, ("", "•"))

    prefix = f"<b>{short}</b> " if short else ""

    line = f"{emoji} <b>{time_str}</b> — {prefix}{subject}"
    if aud:
        line += f" (ауд. {aud})"
    if teachers:
        line += f"\n     👤 {teachers}"
    return line


def format_day(day):
    """Форматирует один день. Дата в формате ДД.ММ.ГГГГ."""
    # day["date"] приходит как "2026-10-05" (ISO) → надо перевернуть
    parts = day["date"].split("-")
    if len(parts) == 3:
        y, mo, d = parts
        date_ru = f"{d}.{mo}.{y}"       # 05.10.2026
    else:
        date_ru = day["date"]           # на всякий случай

    wday = day["wday"]
    wd_name = WEEKDAYS[wday - 1] if 1 <= wday <= 7 else "?"

    lines = [f"📅 <b>{wd_name}, {date_ru}</b>"]

    if not day.get("rec"):
        lines.append("— нет занятий —")
    else:
        for rec in day["rec"]:
            lines.append(_format_lesson(rec))

    return "\n".join(lines)

    if not day.get("rec"):
        lines.append("— нет занятий —")
    else:
        for rec in day["rec"]:
            lines.append(_format_lesson(rec))

    return "\n".join(lines)


def format_all(schedule):
    """Всё расписание с разделителями между днями."""
    out = [f"🗓 <b>Расписание группы {schedule['gname']}</b>\n"]
    days = schedule.get("day", [])
    for i, day in enumerate(days):
        out.append(format_day(day))
        if i < len(days) - 1:
            out.append("▬▬▬▬▬▬▬▬▬▬▬▬")
            out.append("")
    return "\n".join(out).strip()


def format_today(schedule):
    """Расписание на сегодня (или ближайший день)."""
    today = date.today().isoformat()
    days = schedule.get("day", [])

    for day in days:
        if day["date"] == today:
            return format_day(day)

    for day in days:
        if day["date"] >= today:
            return format_day(day)

    return "На ближайшие дни занятий нет 😴"

def format_tomorrow(schedule):
    """Расписание на завтра (или на ближайший будущий день)."""
    from datetime import date, timedelta
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    days = schedule.get("day", [])

    for day in days:
        if day["date"] == tomorrow:
            return format_day(day)

    # Если завтра нет (например, воскресенье) — берём ближайший будущий день
    for day in days:
        if day["date"] >= tomorrow:
            return format_day(day)

    return "На завтра занятий нет 😴"


def format_weekday(schedule, weekday_index):
    """
    Расписание на конкретный день недели.
    weekday_index: 0=Пн, 1=Вт, ..., 5=Сб
    """
    target_wday = weekday_index + 1
    days = schedule.get("day", [])

    for day in days:
        if day["wday"] == target_wday:
            return format_day(day)

    return f"В этот день ({WEEKDAYS[weekday_index]}) занятий нет 😴"


if __name__ == "__main__":
    sched = get_schedule()
    print("Группа:", sched["gname"])
    print("=" * 40)
    print(format_today(sched))
    print("=" * 40)
    print(format_weekday(sched, 0))  # Пн