import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import logic
import keyboards

TOKEN = ""
bot = Bot(token=TOKEN)
dp = Dispatcher()

REPORT_INFO = {
    "schedule": {
        "title": "РАСПИСАНИЕ ГРУПП",
        "desc": "Анализ занятий на неделю для группы.\nПодсчитывает количество пар."
    },
    "topics": {
        "title": "ТЕМЫ ЗАНЯТИЙ",
        "desc": "Проверка формата записей тем.\nФормат: «Урок № _. Тема: _»."
    },
    "students": {
        "title": "УСПЕВАЕМОСТЬ",
        "desc": "Поиск студентов в зоне риска.\nКритерии: ДЗ = 1 или классная работа < 3."
    },
    "attendance": {
        "title": "НИЗКАЯ ПОСЕЩАЕМОСТЬ",
        "desc": "Контроль посещаемости у преподавателей.\nКритерий: ниже 40%."
    },
    "hw_check": {
        "title": "ПРОВЕРКА ДЗ (УЧИТЕЛЯ)",
        "desc": "Анализ проверки заданий педагогами.\nКритерий: процент проверки ниже 70%."
    },
    "hw_submit": {
        "title": "СДАЧА ДЗ (СТУДЕНТЫ)",
        "desc": "Анализ сдачи работ студентами.\nКритерий: процент сдачи ниже 70%."
    }
}


class BotStates(StatesGroup):
    waiting_for_file = State()
    viewing_report = State()
    waiting_for_page = State()


@dp.message(Command("start"))
@dp.callback_query(F.data == "main_menu")
async def cmd_start(event: [Message, CallbackQuery], state: FSMContext):
    await state.clear()

    text = (
        "БОТ УЧЕБНОЙ ЧАСТИ\n"
        "------------------------------------\n"
        "Выберите инструмент анализа:"
    )

    if isinstance(event, Message):
        await event.answer(text, reply_markup=keyboards.main_menu())
    else:
        await event.message.edit_text(text, reply_markup=keyboards.main_menu())


@dp.callback_query(F.data.startswith("report_"))
async def handle_report_btn(callback: CallbackQuery, state: FSMContext):
    report_type = callback.data.replace("report_", "")
    info = REPORT_INFO.get(report_type, {"title": report_type.upper(), "desc": ""})

    await state.update_data(report_type=report_type)
    await state.set_state(BotStates.waiting_for_file)

    text = (
        f"ВЫБРАН ОТЧЕТ: {info['title']}\n\n"
        f"{info['desc']}\n"
        "------------------------------------\n"
        "Жду файл: загрузите таблицу .xlsx"
    )
    await callback.message.edit_text(text, reply_markup=keyboards.back_to_menu())


@dp.message(BotStates.waiting_for_file, F.document)
async def handle_file(message: Message, state: FSMContext):
    data = await state.get_data()
    rtype = data.get("report_type")

    file_info = await bot.get_file(message.document.file_id)
    path = f"temp_{message.document.file_id}.xlsx"
    await bot.download_file(file_info.file_path, path)

    msg = await message.answer("Анализ данных...")

    try:
        if rtype == "schedule":
            res = logic.parse_horizontal_schedule(path)
        elif rtype == "topics":
            res = logic.get_topic_errors(path)
        elif rtype == "students":
            res = logic.get_student_report(path)
        elif rtype == "attendance":
            res = logic.get_attendance_report(path)
        elif rtype == "hw_check":
            res = logic.get_hw_check_report(path)
        elif rtype == "hw_submit":
            res = logic.get_hw_submit_report(path)

        if isinstance(res, list):
            title = REPORT_INFO.get(rtype, {}).get("title", "ОТЧЕТ")
            total = (len(res) + 9) // 10

            await state.update_data(
                items=res,
                page=0,
                total_pages=int(total),
                report_title=title,
                report_msg_id=int(msg.message_id)
            )
            await state.set_state(BotStates.viewing_report)

            await msg.edit_text(
                logic.get_page_text(title, res, 0),
                reply_markup=keyboards.get_pagination_kb(0, total)
            )
        else:
            await msg.edit_text(
                f"РЕЗУЛЬТАТ\n------------------------------------\n\n{res}",
                reply_markup=keyboards.back_to_menu()
            )
            await state.set_state(None)

    except Exception as e:
        await msg.edit_text(f"ОШИБКА: {e}", reply_markup=keyboards.back_to_menu())
    finally:
        if os.path.exists(path):
            os.remove(path)


@dp.callback_query(F.data.startswith("page_"), BotStates.viewing_report)
async def process_pagination(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    new_page = int(callback.data.split("_")[1])

    await state.update_data(page=new_page)
    await callback.message.edit_text(
        logic.get_page_text(data['report_title'], data['items'], new_page),
        reply_markup=keyboards.get_pagination_kb(new_page, data['total_pages'])
    )


@dp.callback_query(F.data == "jump_to_page", BotStates.viewing_report)
async def jump_request(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(BotStates.waiting_for_page)

    prompt = await callback.message.answer(f"Введите номер страницы (1-{data['total_pages']}):")
    await state.update_data(prompt_id=prompt.message_id)


@dp.message(BotStates.waiting_for_page)
async def process_page_num(message: Message, state: FSMContext):
    data = await state.get_data()

    if not message.text.isdigit():
        return

    val = int(message.text)
    if val < 1 or val > data['total_pages']:
        return

    page_idx = val - 1
    await state.update_data(page=page_idx)

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data['report_msg_id'],
        text=logic.get_page_text(data['report_title'], data['items'], page_idx),
        reply_markup=keyboards.get_pagination_kb(page_idx, data['total_pages'])
    )

    await state.set_state(BotStates.viewing_report)

    try:
        await message.delete()
        await bot.delete_message(message.chat.id, data['prompt_id'])
    except:
        pass


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
