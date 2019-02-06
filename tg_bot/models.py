import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Bot(models.Model):
    token = models.CharField(max_length=128, unique=True, verbose_name='Токен')

    def save(self, *args, **kwargs):
        if Bot.objects.exists() and not self.pk:
            raise ValidationError('There is can be only one Bot instance')
        return super(Bot, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.token}'


class User(models.Model):
    S_MAIN_MENU = '0'
    S_HABIT_CHOOSE = '1.0'
    S_HABIT_TITLE_INPUT = '1.0.1'
    S_HABIT_NOTIFICATION_TEXT_INPUT = '1.0.2'
    S_HABIT_START_TIME = '1.1'
    S_HABIT_END_TIME = '1.2'
    S_HABIT_NOTIFICATION_FREQUENCY = '1.3'
    S_WEEKLY_PROGRESS_CONFIRMATION = '2.0'
    S_ARTICLE_CONFIRMATION = '3.0'
    S_ARTICLE_TIME = '3.1'
    S_TIMER_DURATION = '6.0'

    STATE_CHOICES = (
        (S_MAIN_MENU, 'Главное меню'),
        (S_HABIT_CHOOSE, 'Выбор привычки'),
        (S_HABIT_TITLE_INPUT, 'Ввод своей привычки'),
        (S_HABIT_START_TIME, 'Ввод времени начала уведомлений'),
        (S_HABIT_END_TIME, 'Ввод времени прекращения уведомлений'),
        (S_HABIT_NOTIFICATION_FREQUENCY, 'Ввод частоты уведомлений'),
        (S_WEEKLY_PROGRESS_CONFIRMATION, 'Еженедельные сводки'),
        (S_ARTICLE_CONFIRMATION, 'Ежедневные статьи'),
        (S_ARTICLE_TIME, 'Ввод времени получения статей'),
        (S_TIMER_DURATION, 'Ввод продолжительности таймера'),
    )

    user_id = models.IntegerField(primary_key=True)
    state = models.CharField(max_length=8, choices=STATE_CHOICES)

    is_subscribed_to_weekly_progression = models.BooleanField(default=False)
    last_weekly_progression_date = models.DateField(null=True)

    is_subscribed_to_articles = models.BooleanField(default=False)
    articles_timetable = models.TimeField(null=True)
    last_used_article_id = models.IntegerField(default=0, null=True)
    last_user_article_date = models.DateField(null=True)

    def __str__(self):
        return f'{self.user_id}'


class CommonHabit(models.Model):
    title = models.CharField(max_length=128, default=None, verbose_name='Название')
    notification_text = models.CharField(max_length=128, default=None, verbose_name='Текст уведомлений')
    callback_data = models.CharField(max_length=64, default=None, unique=True)

    def __str__(self):
        return f'{self.title}'

    class Meta:
        verbose_name = 'Привычка'
        verbose_name_plural = 'Привычки'


class Habit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits', blank=True, null=True)
    title = models.CharField(max_length=128, default='')
    notification_text = models.CharField(max_length=128, default='')


class Schedule(models.Model):
    habit = models.OneToOneField(Habit, on_delete=models.CASCADE, related_name='schedule')
    date = models.DateField(auto_now=True)
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)


class Notification(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='notifications')
    time = models.TimeField(null=True)
    is_fulfilled = models.BooleanField(default=False)

    confirmation_callback_data = models.CharField(max_length=64, default=None)
    denial_callback_data = models.CharField(max_length=64, default=None)

    def save(self, *args, **kwargs):
        if not self.confirmation_callback_data:
            self.confirmation_callback_data = f'true_{str(uuid.uuid4())}'
        if not self.denial_callback_data:
            self.denial_callback_data = f'false_{str(uuid.uuid4())}'

        super(Notification, self).save(*args, **kwargs)


class Article(models.Model):
    title = models.CharField(max_length=256, null=True, verbose_name='Заголовок')
    text = models.CharField(max_length=2048, verbose_name='Текст')

    def __str__(self):
        return f'{self.title}'

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'


class Timer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='timers', blank=True, null=True)
    duration = models.IntegerField(null=True)
    start_time = models.DateTimeField(auto_now=True)

    callback_data = models.CharField(max_length=64, default=None)

    def save(self, *args, **kwargs):
        if not self.callback_data:
            self.callback_data = f'timer_{str(uuid.uuid4())}'

        super(Timer, self).save(*args, **kwargs)
