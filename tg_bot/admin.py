from django.contrib import admin

from tg_bot.models import CommonHabit, Article, Bot, User


admin.site.register(Bot)
admin.site.register(CommonHabit)
admin.site.register(Article)
