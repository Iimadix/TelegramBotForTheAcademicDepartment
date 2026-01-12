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
    end = start + items_per_page
    current_items = items_list[start:end]

    text = f"💎 {title}\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "\n\n".join(current_items)
    text += "\n\n━━━━━━━━━━━━━━━━━━━━\n"
    text += f"📂 Страница: {page + 1} из {total_pages}\n"
    text += f"📊 Всего записей: {len(items_list)}"

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
                    subj = cell.split("Предмет:")[1].split("Группа:")[0].split("Препод.:")[0].strip()
                    all_entries.append(subj)

    counts = Counter(all_entries)

    if not counts:
        return "❌ Данные не обнаружены\nПроверьте формат файла."

    res = "📅 АНАЛИЗ РАСПИСАНИЯ\n"
    res += "━━━━━━━━━━━━━━━━━━━━\n"

    for subj, count in counts.items():
        res += f"📘 {subj}\n└  Занятий: {count} шт.\n\n"

    res += "━━━━━━━━━━━━━━━━━━━━\n"
    res += f"✅ Итого: {sum(counts.values())} пар за неделю."

    return res


def get_topic_errors(file_path):
    df = pd.read_excel(file_path)
    fio_col = find_col(df, ['ФИО преподавателя', 'препод'])
    topic_col = find_col(df, ['Тема урока', 'тема'])

    if not fio_col or not topic_col:
        return ["❌ Колонки не найдены"]

    errors = []
    for _, row in df.iterrows():
        topic = str(row[topic_col]).strip()

        if not re.match(r"^Урок № \d+\. Тема: .+$", topic):
            errors.append(f"👤 {row[fio_col]}\n└  📝 {topic}")

    return errors


def get_student_report(file_path):
    df = pd.read_excel(file_path)
    fio_col = find_col(df, ['FIO', 'ФИО', 'Студент'])
    group_col = find_col(df, ['Группа', 'Group'])
    hw_col = find_col(df, ['Homework', 'Домашняя'])
    cr_col = find_col(df, ['Classroom', 'Классная'])

    if not all([fio_col, hw_col, cr_col]):
        return "❌ Необходимые колонки не найдены (нужны ФИО, Homework, Classroom)"

    df[hw_col] = pd.to_numeric(df[hw_col], errors='coerce')
    df[cr_col] = pd.to_numeric(df[cr_col], errors='coerce')

    bad_students = df[(df[hw_col] == 1) | (df[cr_col] < 3)].copy()

    if bad_students.empty:
        return "✅ Критичных студентов нет\nВсе успевают!"

    res_list = []
    for _, r in bad_students.iterrows():
        student_info = (
            f"👤 {r[fio_col]}\n"
            f"Группа: {r[group_col] if group_col else 'Не указана'}\n"
            f"Классная работа: {int(r[cr_col]) if not pd.isna(r[cr_col]) else 0}\n"
            f"Домашняя работа: {int(r[hw_col]) if not pd.isna(r[hw_col]) else 0}"
        )
        res_list.append(student_info)

    return res_list


def get_attendance_report(file_path):
    df = pd.read_excel(file_path)
    fio = find_col(df, ['ФИО преподавателя', 'препод'])
    att = find_col(df, ['Средняя посещаемость', 'посещаемость'])

    if not fio or not att:
        return "❌ Колонки не найдены"

    df[att] = (
        df[att].astype(str)
        .str.replace('%', '')
        .str.replace(',', '.')
        .pipe(pd.to_numeric, errors='coerce')
    )

    low_att = df[(df[fio].astype(str).str.lower() != 'всего') & (df[att] < 40)].dropna(subset=[fio])

    if low_att.empty:
        return "✅ Посещаемость в норме"

    return [f"👤 {r[fio]}\n└  📉 Посещаемость: {int(r[att])}%" for _, r in low_att.iterrows()]


def get_hw_check_report(file_path):
    df = pd.read_excel(file_path, skiprows=1)
    df = df.dropna(subset=[df.columns[1]])
    df = df[~df[df.columns[1]].astype(str).str.contains('Всего|Итого', case=False)]

    res_list = []
    for _, row in df.iterrows():
        name = row[df.columns[1]]

        try:
            issued = pd.to_numeric(row[df.columns[3]], errors='coerce') or 0
            checked = pd.to_numeric(row[df.columns[5]], errors='coerce') or 0

            if issued > 0:
                percent = (checked / issued) * 100
                if percent < 70:
                    res_list.append(
                        f"👤 {name}\n"
                        f"└  Выдано: {int(issued)} | Проверено: {int(checked)}\n"
                        f"└  📊 Процент проверки: {int(percent)}%"
                    )
        except Exception:
            continue

    return res_list if res_list else "✅ Проблем с проверкой нет (все выше 70%)"


def get_hw_submit_report(file_path):
    df = pd.read_excel(file_path)
    fio = find_col(df, ['FIO', 'ФИО', 'Студент'])
    pct_col = find_col(df, ['Percentage Homework'])

    if not fio or not pct_col:
        return "❌ Колонки не найдены"

    target_data = df[pct_col]
    if isinstance(target_data, pd.DataFrame):
        target_data = target_data.iloc[:, -1]

    df['val'] = pd.to_numeric(target_data, errors='coerce').fillna(0)
    low_submit = df[(df['val'] < 70) & (df['val'] > 0)]

    if low_submit.empty:
        return "✅ Все студенты сдали ДЗ"

    return [f"👤 {row[fio]}\n└  📤 Сдано ДЗ: {int(row['val'])}%" for _, row in low_submit.iterrows()]