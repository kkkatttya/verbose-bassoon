from datetime import datetime, timedelta
from celery import task

from tg_bot.main import bot, generate_boolean_keyboard
from tg_bot.models import User, Notification, Timer
from tg_bot.utils import find_next_article, generate_progress_report, calculate_timer_time_left

# Monday is 0 and Sunday is 6
WEEKLY_PROGRESSION_DAY_AS_INTEGER = 6
WEEKLY_PROGRESSION_PERIOD_IN_DAYS = 7


@task
def send_article(user_id):
    article_text = find_next_article(user_id)
    bot.send_message(user_id, article_text)


@task
def send_weekly_progression(user_id):
    text = generate_progress_report(user_id, period_in_days=WEEKLY_PROGRESSION_PERIOD_IN_DAYS)
    if text:
        bot.send_message(user_id, text)


@task
def send_notification(user_id, notification_id):
    notification = Notification.objects.get(id=notification_id)
    bot.send_message(user_id, notification.habit.notification_text,
                     reply_markup=generate_boolean_keyboard(notification.confirmation_callback_data,
                                                            notification.denial_callback_data))


@task
def send_timer_end(user_id, timer_id):
    timer = Timer.objects.get(id=timer_id)
    bot.send_message(user_id, f'Таймер на {timer.duration} минут завершен. Повторить?',
                     reply_markup=generate_boolean_keyboard(f'yes_timer_{timer.id}', f'no_timer_{timer.id}'))


@task
def examine_users():
    users = User.objects.all()

    today_date = datetime.now().date()
    now_time = datetime.now().time()
    now_time = (datetime.min + timedelta(hours=now_time.hour, minutes=now_time.minute)).time()

    for user in users:
        # article part
        if user.is_subscribed_to_articles \
                and today_date > user.last_user_article_date \
                and now_time == user.articles_timetable:
            send_article.delay(user.user_id)

        # weekly progression part
        if datetime.today().weekday() == WEEKLY_PROGRESSION_DAY_AS_INTEGER \
                and user.is_subscribed_to_weekly_progression \
                and today_date != user.last_weekly_progression_date:
            send_weekly_progression.delay(user.user_id)

        # notification part
        habits = user.habits.filter(schedule__end_time__isnull=False)
        for habit in habits:
            if habit.schedule.date == today_date and habit.schedule.start_time < now_time < habit.schedule.end_time:
                notification = habit.notifications.filter(time=now_time).last()
                if notification:
                    send_notification.delay(user.user_id, notification.id)

        # timer part
        timers = user.timers.all()
        for timer in timers:
            if calculate_timer_time_left(timer.start_time, timer.duration) == 0:
                send_timer_end.delay(user.user_id, timer.id)
