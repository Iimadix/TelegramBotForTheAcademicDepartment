from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu():
    buttons = [
        [
            InlineKeyboardButton(text="📅 Расписание", callback_data="report_schedule"),
            InlineKeyboardButton(text="📝 Темы", callback_data="report_topics")
        ],
        [
            InlineKeyboardButton(text="👨‍🎓 Успеваемость", callback_data="report_students"),
            InlineKeyboardButton(text="📉 Посещаемость", callback_data="report_attendance")
        ],
        [
            InlineKeyboardButton(text="✅ Проверка ДЗ", callback_data="report_hw_check"),
            InlineKeyboardButton(text="📥 Сдача ДЗ", callback_data="report_hw_submit")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Вернуться назад", callback_data="main_menu")]
    ])


def get_pagination_kb(page: int, total_pages: int):
    buttons = []
    nav_row = []

    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))

    nav_row.append(InlineKeyboardButton(text=f"📄 {page + 1} / {total_pages}", callback_data="none"))

    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))

    buttons.append(nav_row)

    if total_pages > 1:
        buttons.append([
            InlineKeyboardButton(text="🔢 Перейти к странице...", callback_data="jump_to_page")
        ])

    buttons.append([
        InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)