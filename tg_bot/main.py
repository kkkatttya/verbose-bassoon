import os
import sys

import django
import telebot

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "habit_bot.settings")
django.setup()

import tg_bot.messages as messages
from tg_bot.models import Bot, User, Habit, Schedule, CommonHabit, Notification, Timer
from tg_bot.utils import validate_time, split_time_interval_to_sub_intervals, generate_progress_report, \
    calculate_timer_time_left

bot = telebot.TeleBot(Bot.objects.first().token)

MIN_NOTIFICATION_COUNT = 1
MAX_NOTIFICATION_COUNT = 24
PROGRESSION_PERIOD_IN_DAYS = 14


def generate_keyboard(row_width=1, **kwargs):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row_width = row_width
    buttons = list()
    for text, callback_data in kwargs.items():
        buttons.append(telebot.types.InlineKeyboardButton(text=text, callback_data=callback_data))
    keyboard.add(*buttons)
    return keyboard


def generate_boolean_keyboard(true_callback_data='Yes', false_callback_data='No'):
    boolean_buttons = {
        'Да': true_callback_data,
        'Нет': false_callback_data
    }
    return generate_keyboard(row_width=2, **boolean_buttons)


def generate_main_menu_keyboard():
    main_menu_buttons = {
        'Установить уведомление о соблюдении привычки': 'notification',
        'Установить уведомление со сводками за неделю': 'weekly_progress',
        'Мотивационные статьи': 'article',
        'Мой прогресс': 'progress',
        'Инструкция': 'instruction',
        'Таймер': 'set_timer'
    }
    return generate_keyboard(**main_menu_buttons)


def change_user_state(user_id, state):
    user = User.objects.get(user_id=user_id)
    user.state = state
    user.save(update_fields=['state'])


@bot.message_handler(commands=['start'])
def handle_start(message):
    User.objects.get_or_create(user_id=message.from_user.id)
    bot.send_message(message.chat.id, messages.start_message, reply_markup=generate_main_menu_keyboard())
    change_user_state(message.from_user.id, User.S_MAIN_MENU)


@bot.message_handler(commands=['menu'])
def handle_menu(message):
    bot.send_message(message.chat.id, 'Меню', reply_markup=generate_main_menu_keyboard())
    change_user_state(message.from_user.id, User.S_MAIN_MENU)


@bot.callback_query_handler(
    func=lambda call: User.objects.get(user_id=call.message.chat.id).state == User.S_HABIT_CHOOSE)
def handle_habit_choose(call):
    if call.message:
        if call.data == 'personal habit':
            text = 'Введите название привычки'
            change_user_state(call.message.chat.id, User.S_HABIT_TITLE_INPUT)
            bot.send_message(call.message.chat.id, text)
        elif call.data in [common_habit.callback_data for common_habit in CommonHabit.objects.all()]:
            user = User.objects.get(user_id=call.message.chat.id)
            common_habit = CommonHabit.objects.get(callback_data=call.data)
            habit = Habit.objects.create(user=user,
                                         title=common_habit.title,
                                         notification_text=common_habit.notification_text)
            Schedule.objects.create(habit=habit)
            text = 'Введите время начала уведомлений в формате ЧЧ:ММ'
            change_user_state(call.message.chat.id, User.S_HABIT_START_TIME)
            bot.send_message(call.message.chat.id, text)


@bot.callback_query_handler(
    func=lambda call: User.objects.get(user_id=call.message.chat.id).state == User.S_ARTICLE_CONFIRMATION)
def handle_article_confirmation(call):
    if call.message:
        if call.data == 'Yes':
            bot.send_message(call.message.chat.id, 'Введите время отправки статей в формате ЧЧ:ММ')
            change_user_state(call.message.chat.id, User.S_ARTICLE_TIME)
        if call.data == 'Yes' or call.data == 'No':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            change_user_state(call.message.chat.id, User.S_MAIN_MENU)


@bot.callback_query_handler(
    func=lambda call: User.objects.get(user_id=call.message.chat.id).state == User.S_WEEKLY_PROGRESS_CONFIRMATION)
def handle_weekly_progress_confirmation(call):
    if call.message:
        if call.data == 'Yes':
            user = User.objects.get(user_id=call.message.chat.id)
            user.is_subscribed_to_weekly_progression = True
            user.save(update_fields=['is_subscribed_to_weekly_progression'])
        if call.data == 'No':
            user = User.objects.get(user_id=call.message.chat.id)
            user.is_subscribed_to_weekly_progression = False
            user.save(update_fields=['is_subscribed_to_weekly_progression'])
        if call.data == 'Yes' or call.data == 'No':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            change_user_state(call.message.chat.id, User.S_MAIN_MENU)


@bot.callback_query_handler(func=lambda call: call.data.startswith('true') or call.data.startswith('false'))
def handle_notification(call):
    if call.message:
        if call.data.startswith('true'):
            notification = Notification.objects.get(confirmation_callback_data=call.data)
            notification.is_fulfilled = True
        if call.data.startswith('false'):
            notification = Notification.objects.get(denial_callback_data=call.data)
            notification.is_fulfilled = False
        if call.data.startswith('true') or call.data.startswith('false'):
            notification.save(update_fields=['is_fulfilled'])
            bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('timer'))
def handle_notification(call):
    if call.message:
        if call.data:
            timer = Timer.objects.get(callback_data=call.data)
            time_left = calculate_timer_time_left(timer.start_time, timer.duration)
            if time_left:
                bot.send_message(call.message.chat.id, f'Таймер: осталось {time_left} минут')
            else:
                bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('yes_timer') or call.data.startswith('no_timer'))
def handle_notification(call):
    if call.message:
        if call.data:
            timer_id = call.data.split('_')[2]
            if call.data.startswith('yes_timer'):
                timer = Timer.objects.get(id=timer_id)
                timer.save()
                bot.delete_message(call.message.chat.id, call.message.message_id)
            if call.data.startswith('no_timer'):
                bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(
    func=lambda call: User.objects.get(user_id=call.message.chat.id).state == User.S_MAIN_MENU)
def handle_main_menu(call):
    msg = call.message
    if msg:
        if call.data == 'notification':
            habits = {habit.title: habit.callback_data for habit in CommonHabit.objects.all()}
            habits['Добавить свою привычку'] = 'personal habit'
            bot.send_message(msg.chat.id, 'Выберите привычку из списка',
                             reply_markup=generate_keyboard(**habits))
            change_user_state(msg.chat.id, User.S_HABIT_CHOOSE)
        elif call.data == 'weekly_progress':
            bot.send_message(msg.chat.id, 'Установить уведомления со сводками за неделю?',
                             reply_markup=generate_boolean_keyboard())
            change_user_state(msg.chat.id, User.S_WEEKLY_PROGRESS_CONFIRMATION)
        elif call.data == 'article':
            bot.send_message(msg.chat.id, 'Подписаться на получение уведомлений?',
                             reply_markup=generate_boolean_keyboard())
            change_user_state(msg.chat.id, User.S_ARTICLE_CONFIRMATION)
        elif call.data == 'progress':
            bot.send_message(msg.chat.id,
                             generate_progress_report(msg.chat.id, period_in_days=PROGRESSION_PERIOD_IN_DAYS))
        elif call.data == 'instruction':
            bot.send_message(msg.chat.id, messages.instruction_message)
        elif call.data == 'set_timer':
            bot.send_message(msg.chat.id, 'Введите время таймера, в минутах')
            change_user_state(msg.chat.id, User.S_TIMER_DURATION)


@bot.message_handler(
    func=lambda message: User.objects.get(user_id=message.from_user.id).state == User.S_HABIT_TITLE_INPUT,
    content_types=['text'])
def handle_habit_title_input(message):
    user = User.objects.get(user_id=message.from_user.id)
    habit = Habit.objects.create(user=user, title=message.text)
    Schedule.objects.create(habit=habit)
    bot.send_message(message.chat.id, 'Введите текст уведомлений')
    change_user_state(message.from_user.id, User.S_HABIT_NOTIFICATION_TEXT_INPUT)


@bot.message_handler(
    func=lambda message: User.objects.get(user_id=message.from_user.id).state == User.S_HABIT_NOTIFICATION_TEXT_INPUT,
    content_types=['text'])
def handle_habit_notification_text_input(message):
    user = User.objects.get(user_id=message.from_user.id)
    habit = user.habits.last()
    habit.notification_text = message.text
    habit.save(update_fields=['notification_text'])
    bot.send_message(message.chat.id, 'Введите время начала уведомлений в формате ЧЧ:ММ')
    change_user_state(message.from_user.id, User.S_HABIT_START_TIME)


@bot.message_handler(
    func=lambda message: User.objects.get(user_id=message.from_user.id).state == User.S_HABIT_START_TIME,
    content_types=['text'])
def handle_habit_start_time(message):
    time = validate_time(message.text)
    if not time:
        return
    user = User.objects.get(user_id=message.from_user.id)
    habit = user.habits.last()
    habit.schedule.start_time = time
    habit.schedule.save(update_fields=['start_time'])
    bot.send_message(message.chat.id, 'Введите время завершения уведомлений в формате ЧЧ:ММ')
    change_user_state(message.from_user.id, User.S_HABIT_END_TIME)


@bot.message_handler(
    func=lambda message: User.objects.get(user_id=message.from_user.id).state == User.S_HABIT_END_TIME,
    content_types=['text'])
def handle_habit_end_time(message):
    time = validate_time(message.text)
    if not time:
        return
    user = User.objects.get(user_id=message.from_user.id)
    habit = user.habits.last()
    habit.schedule.end_time = time
    habit.schedule.save(update_fields=['end_time'])
    bot.send_message(message.chat.id, f'Введите частоту уведомлений '
                                      f'(от {MIN_NOTIFICATION_COUNT} до {MAX_NOTIFICATION_COUNT} раз за день)')
    change_user_state(message.from_user.id, User.S_HABIT_NOTIFICATION_FREQUENCY)


@bot.message_handler(
    func=lambda message: User.objects.get(user_id=message.from_user.id).state == User.S_HABIT_NOTIFICATION_FREQUENCY,
    content_types=['text'])
def handle_habit_notification_frequency(message):
    try:
        count = int(message.text)
    except ValueError:
        return

    if count < MIN_NOTIFICATION_COUNT or count > MAX_NOTIFICATION_COUNT:
        return

    user = User.objects.get(user_id=message.from_user.id)
    habit = user.habits.last()

    notification_times = split_time_interval_to_sub_intervals(habit.schedule.start_time, habit.schedule.end_time, count)
    for time in notification_times:
        Notification.objects.create(habit=habit, time=time)

    change_user_state(message.chat.id, User.S_MAIN_MENU)


@bot.message_handler(func=lambda message: User.objects.get(user_id=message.from_user.id).state == User.S_ARTICLE_TIME,
                     content_types=['text'])
def handle_article_time_input(message):
    time = validate_time(message.text)
    if time:
        user = User.objects.get(user_id=message.from_user.id)
        user.articles_timetable = time
        user.save(update_fields=['articles_timetable'])
        change_user_state(message.chat.id, User.S_MAIN_MENU)
    else:
        pass


@bot.message_handler(
    func=lambda message: User.objects.get(user_id=message.from_user.id).state == User.S_TIMER_DURATION,
    content_types=['text'])
def handle_habit_title_input(message):
    try:
        minutes = int(message.text)
    except ValueError:
        return

    user = User.objects.get(user_id=message.from_user.id)

    timer = Timer.objects.create(user=user, duration=minutes)
    bot.send_message(message.chat.id, f'Таймер на {minutes} минут активен, время пошло',
                     reply_markup=generate_keyboard(**{'Узнать оставшееся время': timer.callback_data}))

    change_user_state(message.from_user.id, User.S_MAIN_MENU)


if __name__ == '__main__':
    bot.polling(none_stop=True)
