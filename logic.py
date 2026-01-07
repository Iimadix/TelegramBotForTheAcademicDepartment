import pandas as pd
import re
from collections import Counter

def find_col(df, key_words):
    for col in df.columns:
        if any(word.lower() in str(col).lower() for word in key_words):
            return col
    return None

def get_page_text(title, items_list, page, items_per_page=10):
    total_pages = (len(items_list) + items_per_page - 1) // items_per_page
    start = page * items_per_page
    current_items = items_list[start:start + items_per_page]
    text = f"--- {title} ({page + 1}/{total_pages}) ---\n\n"
    text += "\n\n".join(current_items)
    return text

def parse_horizontal_schedule(file_path):
    df = pd.read_excel(file_path)
    all_entries = []
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    for col in df.columns:
        if any(day in str(col) for day in days):
            cells = df[col].dropna().astype(str)
            for cell in cells:
                if "Предмет:" in cell:
                    subj = cell.split("Предмет:")[1].split("Группа:")[0].strip()
                    all_entries.append(subj)
    counts = Counter(all_entries)
    res = "Отчет по расписанию:\n"
    for s, c in counts.items():
        res += f"- {s}: {c} шт.\n"
    return res

def get_topic_errors(file_path):
    df = pd.read_excel(file_path)
    fio_col = find_col(df, ['ФИО преподавателя'])
    topic_col = find_col(df, ['Тема урока'])
    if not fio_col or not topic_col:
        return ["Ошибка: Колонки не найдены"]
    errors = []
    for i, row in df.iterrows():
        topic = str(row[topic_col]).strip()
        if not re.match(r"^Урок № \d+\. Тема: .+$", topic):
            errors.append(f"Преподаватель: {row[fio_col]}\nТема: {topic}")
    return errors

def get_student_report(file_path):
    return "Модуль в разработке."

def get_attendance_report(file_path):
    return "Модуль в разработке."

def get_hw_check_report(file_path):
    return "Модуль в разработке."

def get_hw_submit_report(file_path):
    return "Модуль в разработке."