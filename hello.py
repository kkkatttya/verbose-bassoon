# -*- coding: utf-8 -*-

import config
import telebot
import re

from telebot import types

bot = telebot.TeleBot(config.token)
condition = " "

def get_database():
    sqlite_file = 'D:\Рабочий Стол\Telebot\Bot_db.sqlite'
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    return c

def get_time(id):
    cursor = get_database()
    try:
        reply = cursor.execute('SELECT * FROM NOTIFICATION_TIME WHERE id = ' + str(id))
        all_rows = reply.fetchall()
        print('1):', all_rows)
    except sqlite3.Error:
        bot.send_message(id, "Не установлено время оповещений")

def cancel():
    global condition
    cb_cancel = types.InlineKeyboardButton(text="Назад", callback_data="cancel")
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(cb_btn_cancel)
    return keyboard 


@bot.callback_query_handler(func=lambda call: True)
def all_functions(call):
    global condition
    if call.message:
            if call.data == "notification":
                notification_keyboard(call)
            elif call.data == "start":
                functions_keyboard(call)
            elif call.data == "instruction":
                show_instruction(call)
            elif call.data == "cancel":
                functions_keyboard(call)
            elif call.data == "individual" or "smoke" or "drink" or "read" or "eat" or "dog" or "whine":
                make_notification(call)
            elif call.data == "compet":
            	print(call.data)
                competition(call)
            elif call.data == "timer":
                timer(call)
            elif call.data == "progress":
                show_progress(call)
            elif call.data == "article":
                send_article(call)
            elif call.data == "weeklyprogress":
                show_weekly_progress(call)







@bot.message_handler(content_types=["text"])
def any_msg(message):
    keyboard = types.InlineKeyboardMarkup()
    callback_button = types.InlineKeyboardButton(text="Верно", callback_data="start")
    keyboard.add(callback_button)
    bot.send_message(message.chat.id, "Здравствуй! Я твой бот помощник, как я понимаю ты настроен совершенствоваться в своей продуктивности и правильных привычках, верно?", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def functions_keyboard(call):
    cb_privichka = types.InlineKeyboardButton(text="Установить уведомление о соблюдении привычки", callback_data="notification")
    cb_weekly_progress = types.InlineKeyboardButton(text="Недельный прогресс", callback_data="weeklyprogress")
    cb_articles = types.InlineKeyboardButton(text="Статьи", callback_data="article")
    cb_progress = types.InlineKeyboardButton(text="Мой прогресс", callback_data="progress")
    cb_instruction = types.InlineKeyboardButton(text="Описание", callback_data="instruction")
    cb_timer = types.InlineKeyboardButton(text="Таймер", callback_data="timer")
    cb_competition= types.InlineKeyboardButton(text="Соревнование", callback_data="compet")

    keyboard_functions = types.InlineKeyboardMarkup()
    keyboard_functions.row_width = 1
    keyboard_functions.add(cb_competition, cb_timer, cb_instruction, cb_progress, cb_articles, cb_privichka, cb_weekly_progress)

    bot.send_message(chat_id=call.message.chat.id, text="Отлично, тогда вот тебе мои функций:", reply_markup = keyboard_functions)
    


def show_instruction(message):

    bot.send_message(chat_id=call.message.chat.id, text="Обзор основных функций:\n1. Установить уведомление о соблюдении привычки\n2. Недельный прогресс\n3. Статьи\n4. Мой прогресс\n5. Описание\n6. Таймер\n7. Соревнование")

@bot.callback_query_handler(func=lambda call: True)
def notification_keyboard(call):
    global condition

    priv_1 = types.InlineKeyboardButton(text="Не курить", callback_data="smoke")
    priv_2 = types.InlineKeyboardButton(text="Не пить", callback_data="drink")
    priv_3 = types.InlineKeyboardButton(text="Читать 20 страниц в день", callback_data="read")
    priv_4 = types.InlineKeyboardButton(text="Правильно питаться", callback_data="eat")
    priv_5 = types.InlineKeyboardButton(text="Дрессировать собаку", callback_data="dog")
    priv_6 = types.InlineKeyboardButton(text="Не жаловаться", callback_data="whine")
    priv_7 = types.InlineKeyboardButton(text="Своя привычка", callback_data="individual")
    cb_cancel = types.InlineKeyboardButton(text="Назад", callback_data="cancel")

    keyboard_priv = types.InlineKeyboardMarkup()
    keyboard_priv.row_width = 1
    keyboard_priv.add(priv_1, priv_2, priv_3, priv_4, priv_5, priv_6, priv_7, cb_cancel)
    bot.send_message(chat_id=call.message.chat.id, text="Выбери привычку, которую хочешь соблюдать:", reply_markup = keyboard_priv)

@bot.callback_query_handler(func=lambda call: True)
def make_notification(call):
    global condition

    if call.data == "individual":
        bot.send_message(chat_id=call.message.chat.id, text='Набери свой текст, который будет высвечиваться в уведомлении о привычке.')
        
    elif call.data == "smoke":
        bot.send_message(chat_id=call.message.chat.id, text='1 сигарета = - 15 минут жизни')

    elif call.data == "drink":
        bot.send_message(chat_id=call.message.chat.id, text='Не запивай горе')

    elif call.data == "read":
        bot.send_message(chat_id=call.message.chat.id, text='Все успешные люди читают книги каждый день, так почему ты еще не в их числе?')

    elif call.data == "eat":
        bot.send_message(chat_id=call.message.chat.id, text='Еда - вознаграждение')

    elif call.data == "dog":
        bot.send_message(chat_id=call.message.chat.id, text='Пресказуемая собака = спокойствие хозяина')

    elif call.data == "whine":
        bot.send_message(chat_id=call.message.chat.id, text='Чем больше жалуешься, тем в бОльший негатив погружешься')


def show_weekly_progress(call):
    bot.send_message(chat_id=call.message.chat.id, text='Ты на этой неделе:')
    
def send_article(call):
    article_url = open(config.py, 'rb')
    bot.inline_query_result_article(chat_id=call.message.chat.id, type=article, id=article, title=article, url=article_url)
    
def show_progress(call):
    bot.send_message(chat_id=call.message.chat.id, text='Твой прогресс:')
    
def timer(call):
    bot.send_message(chat_id=call.message.chat.id, text='Выбери время таймера')
    
def competition(call):
    bot.send_message(chat_id=call.message.chat.id, text='Введи свое имя:')
    


if __name__ == '__main__':
     bot.polling(none_stop = True)