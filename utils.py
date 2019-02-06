from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from tg_bot.models import User, Article


def find_next_article(user_id):
    user = User.objects.get(user_id=user_id)
    articles = Article.objects.all().order_by('id')

    article = next((article for article in articles if article.id > user.last_used_article_id), articles[0])

    user.last_used_additional_text_id = article.id
    user.save(update_fields=['last_used_article_id'])

    return f'{article.title}\n{article.text}' if article.title else article.text


def validate_time(time):
    try:
        return datetime.strptime(time, '%H:%M').time()
    except ValueError:
        return None


def split_time_interval_to_sub_intervals(start_time, end_time, number_of_intervals):
    start_time = timedelta(hours=start_time.hour, minutes=start_time.minute)
    end_time = timedelta(hours=end_time.hour, minutes=end_time.minute)
    time_delta = end_time - start_time
    intervals = list()
    for i in range(1, number_of_intervals + 1):
        total_seconds = start_time.total_seconds() + time_delta.total_seconds() / number_of_intervals * i
        intervals.append((datetime.min + timedelta(seconds=total_seconds)).time())
    return intervals


def calculate_n_days_ago_date(n_days):
    return datetime.today().date() + relativedelta(days=-n_days)


def generate_progress_report(user_id, period_in_days):
    end_date = datetime.today().date()
    start_date = calculate_n_days_ago_date(period_in_days)

    user = User.objects.get(user_id=user_id)
    habits = user.habits.filter(schedule__end_time__isnull=False,
                                schedule__date__gte=start_date,
                                schedule__date__lte=end_date)

    text = f'Ваш прогресс за последние {period_in_days} дней:'
    for habit in habits:
        text += f'\n{habit.schedule.date.strftime("%d.%m.%Y")} ' \
                f'{habit.schedule.start_time.strftime("%H:%M")} - {habit.schedule.end_time.strftime("%H:%M")} ' \
                f'{habit.title}, ' \
                f'выполнено {habit.notifications.filter(is_fulfilled=True).count()}/{habit.notifications.count()}'

    return text


def calculate_timer_time_left(start_time, duration):
    start_time = timedelta(hours=start_time.hour, minutes=start_time.minute).total_seconds()
    now_time = datetime.now().time()
    now_time = timedelta(hours=now_time.hour, minutes=now_time.minute).total_seconds()
    duration = timedelta(minutes=duration).total_seconds()
    if start_time + duration >= now_time:
        return (start_time + duration - now_time) / 60
    else:
        return None
