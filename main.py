import os, asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logic, keyboards

TOKEN = ""
bot = Bot(token=TOKEN)
dp = Dispatcher()

class BotStates(StatesGroup):
    waiting_for_file = State()
    viewing_report = State()
    waiting_for_page = State()

@dp.message(Command("start"))
@dp.callback_query(F.data == "main_menu")
async def cmd_start(event: [Message, CallbackQuery], state: FSMContext):
    await state.clear()
    text = "Система учебной части\nВыберите инструмент:"
    if isinstance(event, Message):
        await event.answer(text, reply_markup=keyboards.main_menu())
    else:
        await event.message.edit_text(text, reply_markup=keyboards.main_menu())

@dp.callback_query(F.data.startswith("report_"))
async def handle_report_btn(callback: CallbackQuery, state: FSMContext):
    report_type = callback.data.replace("report_", "")
    await state.update_data(report_type=report_type)
    await state.set_state(BotStates.waiting_for_file)
    await callback.message.edit_text(
        f"Выбран отчет: {report_type}\nОтправьте файл .xlsx",
        reply_markup=keyboards.back_to_menu()
    )

@dp.message(BotStates.waiting_for_file, F.document)
async def handle_file(message: Message, state: FSMContext):
    data = await state.get_data()
    rtype = data.get("report_type")
    path = f"temp_{message.document.file_id}.xlsx"
    await bot.download_file((await bot.get_file(message.document.file_id)).file_path, path)
    msg = await message.answer("Обработка...")
    try:
        if rtype == "schedule":
            res = logic.parse_horizontal_schedule(path)
        elif rtype == "topics":
            errors = logic.get_topic_errors(path)
            if isinstance(errors, list) and len(errors) > 0:
                total = (len(errors) + 9) // 10
                await state.update_data(items=errors, page=0, total_pages=total, report_title="Ошибки тем", report_msg_id=msg.message_id)
                await state.set_state(BotStates.viewing_report)
                await msg.edit_text(logic.get_page_text("Ошибки тем", errors, 0), reply_markup=keyboards.get_pagination_kb(0, total))
                return
            res = "Ошибок не найдено."
        else:
            if rtype == "students": res = logic.get_student_report(path)
            elif rtype == "attendance": res = logic.get_attendance_report(path)
            elif rtype == "hw_check": res = logic.get_hw_check_report(path)
            elif rtype == "hw_submit": res = logic.get_hw_submit_report(path)

        await msg.edit_text(res, reply_markup=keyboards.back_to_menu())
    except Exception as e:
        await msg.edit_text(f"Ошибка: {e}")
    finally:
        if os.path.exists(path): os.remove(path)

@dp.callback_query(F.data.startswith("page_"))
async def process_pagination(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    new_page = int(callback.data.split("_")[1])
    await state.update_data(page=new_page)
    await callback.message.edit_text(
        logic.get_page_text(data['report_title'], data['items'], new_page),
        reply_markup=keyboards.get_pagination_kb(new_page, data['total_pages'])
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())