import shelve

import telebot
import time
from telebot import types
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import os

from threading import Timer

class Event(FileSystemEventHandler):

    def on_created(self, event):
        if event.is_directory == False:
            if event.src_path in '{:s}{:s}'.format(workpath, update_mark):
                chat = None
                with shelve.open(chats_storage) as chats:
                    with shelve.open(data_storage) as storage:
                        for chat_id, identifier in chats.items():
                            try:
                                chat = chat_id
                                if identifier in storage:
                                    for date_key, values in storage[identifier].items():
                                        response = '<b>{:s}\n{:s}</b>\n{:s}'.format(date_key, values[0], values[1])
                                        delete_message(chat_id, bot.send_message(chat_id, response, parse_mode='html').message_id, 43200)
                            except:
                                id_message_error = bot.send_message(chat, 'При обновлении сведений произошла ошибка.', parse_mode='html').message_id
                                delete_message(chat_id, id_message_error, 43200)
                os.remove(event.src_path)
                                

token = # токен бота
data_storage = # путь к БД Shelve, которая хранит данные, отсылаемые пользователям (график работы)
chats_storage = # путь к БД Shelve, которая хранит чаты пользователей, которые подписаны на оповещения
workpath = # путь к директории, в которой проверяется наличие маркера оповещения - файла, хранящегося в переменной update_mark
update_mark = 'update.mark' # файл-маркер для оповещения

id_messages = list()

bot = telebot.TeleBot(token, threaded=False)

observer = Observer()
event_handler = Event()
observer.schedule(event_handler, workpath, recursive=False)
observer.start()

@bot.message_handler(commands=['start'])
def start_command(message):
    delete_message(message.chat.id, bot.send_message(message.chat.id, 'Привет, напиши номер.').message_id)

def save_id(message, removed_message_id):
    with shelve.open(chats_storage, 'c') as storage:
        storage[str(message.chat.id)] = message.text
    msg = bot.send_message(message.chat.id, 'Твой номер добавлен в рассылку')
    delete_message(message.chat.id, message.message_id)
    delete_message(message.chat.id, removed_message_id)
    delete_message(message.chat.id, msg.message_id)

@bot.message_handler(commands=['whois'])
def start_command(message):
    response = 'Извини, но я ничего не нашел!'
    with shelve.open(data_storage, 'r') as storage:
        if 'отв' in storage:
            for date_key, values in storage['отв'].items():
                response = '<b>{:s}\n{:s}</b>\n{:s}'.format(date_key, values[0], values[1])
                msg = bot.send_message(message.chat.id, response, parse_mode='html')
                delete_message(message.chat.id, msg.message_id)
        else:
            bot.send_message(message.chat.id, response, parse_mode='html')
    delete_message(message.chat.id, message.message_id)

# рассылка всем подписчикам сообщения от отправителя данной команды (сообщение прописывается после команды с пробелом)
@bot.message_handler(commands=['all'])
def start_command(message):
    text = message.text.split(' ', 1)[1:]
    with shelve.open(chats_storage) as chats:
        for chat_id, identifier in chats.items():
            delete_message(chat_id, bot.send_message(chat_id, text, parse_mode='html').message_id, 43200)

@bot.message_handler(commands=['delete'])
def set_id(message):
    with shelve.open(chats_storage, 'c') as storage:
        del storage[str(message.chat.id)]
    msg = bot.send_message(message.chat.id, 'Твой номер удалён из рассылки.')
    delete_message(message.chat.id, msg.message_id)
    delete_message(message.chat.id, message.message_id)

@bot.message_handler(commands=['set'])
def set_id(message):    
    board = types.InlineKeyboardMarkup()
    cancel = types.InlineKeyboardButton(text='Отмена', callback_data='Отмена')
    board.add(cancel)

    msg = bot.send_message(message.chat.id, 'Напиши мне свой номер, чтобы я его добавил в рассылку.', reply_markup=board)
    bot.register_next_step_handler(msg, lambda m: save_id(m, msg.message_id))

    delete_message(message.chat.id, message.message_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data == 'Отмена':
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Отменено.')
            delete_message(call.message.chat.id, call.message.message_id)

@bot.message_handler(commands=['get'])
def get(message):
    chat_id = str(message.chat.id)
    response = 'Извини, ты наверно ошибся, я ничего не нашел!'
    with shelve.open(data_storage, 'r') as storage:
        with shelve.open(chats_storage) as chats:
            if chat_id in chats:
                if chats[chat_id] in storage:
                    identificator = chats[chat_id]
                    for date_key, values in storage[identificator].items():
                        response = '<b>{:s}\n{:s}</b>\n{:s}'.format(date_key, values[0], values[1])
                        msg = bot.send_message(message.chat.id, response, parse_mode='html')
                        delete_message(message.chat.id, msg.message_id)
                else:
                    delete_message(message.chat.id, bot.send_message(message.chat.id, response, parse_mode='html').message_id)
    delete_message(message.chat.id, message.message_id)

@bot.message_handler(content_types=['text'])
def received_text(message):
    response = 'Извини, ты наверно ошибся, я ничего не нашел!'
    with shelve.open(data_storage, 'r') as storage:
        if message.text in storage:
            for date_key, values in storage[message.text].items():
                response = '<b>{:s}\n{:s}</b>\n{:s}'.format(date_key, values[0], values[1])
                msg = bot.send_message(message.chat.id, response, parse_mode='html')
                delete_message(message.chat.id, msg.message_id)
        else:
            delete_message(message.chat.id, bot.send_message(message.chat.id, response, parse_mode='html').message_id)
    delete_message(message.chat.id, message.message_id)

def delete_message(chat_id, message_id, seconds = 60.0):
    Timer(seconds, bot.delete_message, [chat_id, message_id]).start()

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        time.sleep(15)