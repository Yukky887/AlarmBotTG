import telebot
from telebot import types
from telebot.types import Message
from datetime import datetime, timedelta
import time
from threading import Thread
from wakeonlan import send_magic_packet  # Импортируем библиотеку для Wake on LAN

bot = telebot.TeleBot('7577820613:AAGz3c5Blm2z_XXsQXIlU4bMa3GcYDf3KfE')

# Словарь для хранения времени будильников
user_alarms = {}

# Используем словарь для хранения состояний пользователя
user_states = {}

# Словарь для хранения MAC-адресов пользователей
user_mac_addresses = {}

# Функция для отправки уведомлений в заданное время
def check_alarms():
    while True:
        current_time = datetime.now().strftime('%H:%M')  # Текущее время в формате HH:MM
        # Собираем список пользователей, у которых сработал будильник
        users_to_notify = [user_id for user_id, alarm_time in user_alarms.items() if alarm_time == current_time]

        # Отправляем уведомления пользователям
        for user_id in users_to_notify:
            file = open('./photo_cat.jpg', 'rb')
            bot.send_photo(user_id, photo=file)
            bot.send_message(user_id, f"⏰ Время для вашего будильника: {user_alarms[user_id]}!")

            # Проверяем, если у пользователя есть MAC-адрес, отправляем magic packet
            if user_id in user_mac_addresses:
                target_mac_address = user_mac_addresses[user_id]
                send_magic_packet(target_mac_address)  # Отправка magic packet

            del user_alarms[user_id]  # Удаляем будильник после его активации

        time.sleep(60)  # Проверяем раз в минуту


# Запускаем проверку будильников в отдельном потоке
def start_alarm_thread():
    thread = Thread(target=check_alarms)
    thread.daemon = True
    thread.start()


# Запуск проверки будильников
start_alarm_thread()


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Используем ReplyKeyboardMarkup

    # Создание кнопок
    btn1 = types.KeyboardButton('Завести будильник')
    btn2 = types.KeyboardButton('Мой будильник')
    btn3 = types.KeyboardButton('Мой mac')
    btn4 = types.KeyboardButton('Help')

    # Добавляем кнопки в строку
    markup.row(btn1)
    markup.row(btn2, btn3)
    markup.row(btn4)

    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name} {message.from_user.last_name}',
                     reply_markup=markup)


# Обработчик нажатий на кнопку "Завести будильник"
@bot.message_handler(func=lambda message: message.text == 'Завести будильник')
def ask_time(message):
    markup = types.InlineKeyboardMarkup()

    btn1 = types.InlineKeyboardButton('Ввести своё время', callback_data='write_time')
    btn2 = types.InlineKeyboardButton('Завести на 06:30', callback_data='06:30')
    btn3 = types.InlineKeyboardButton('Завести на 08:30', callback_data='08:30')
    btn4 = types.InlineKeyboardButton('Завести на 10:00', callback_data='10:00')

    markup.row(btn1)
    markup.row(btn2, btn3, btn4)

    bot.send_message(message.chat.id, 'Во сколько вставать?', reply_markup=markup)


# Обработчик callback'ов для inline кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.message.chat.id

    if call.data == 'write_time':
        # Сохраняем состояние, что пользователь теперь вводит время
        user_states[user_id] = 'waiting_for_time'
        bot.answer_callback_query(call.id, "Введите ваше время в формате HH:MM")
        bot.send_message(call.message.chat.id, "Введите время для будильника, например: 07:30")
    else:
        # Когда выбирают фиксированное время
        bot.answer_callback_query(call.id, f"Будильник установлен на {call.data}")
        user_alarms[user_id] = call.data
        remaining_time = get_remaining_time(call.data)
        bot.send_message(user_id, f"Будильник установлен на {call.data}. Осталось спать: {remaining_time}")


# Обработчик нажатий на кнопку "Мой будильник"
@bot.message_handler(func=lambda message: message.text == 'Мой будильник')
def show_alarms(message):
    user_id = message.chat.id
    if user_id in user_alarms:
        alarm_time = user_alarms[user_id]
        remaining_time = get_remaining_time(alarm_time)
        bot.send_message(user_id, f"Ваш будильник установлен на {alarm_time}. Осталось спать: {remaining_time}.")
    else:
        bot.send_message(user_id, "У вас нет активных будильников.")


# Обработчик нажатий на кнопку "Мой mac" (для ввода/изменения MAC-адреса)
@bot.message_handler(func=lambda message: message.text == 'Мой mac')
def ask_mac_address(message):
    user_id = message.chat.id
    user_states[user_id] = 'waiting_for_mac_address'  # Устанавливаем состояние для ввода MAC-адреса
    bot.send_message(user_id, "Введите MAC-адрес вашего компьютера в формате XX-XX-XX-XX-XX-XX:")


# Обработчик для ввода MAC-адреса пользователем
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'waiting_for_mac_address')
def set_mac_address(message: Message):
    user_id = message.chat.id
    mac_address = message.text.strip()

    # Проверяем, что MAC-адрес введён в правильном формате
    if len(mac_address) == 17 and mac_address.count('-') == 5 and all(x.isalnum() for x in mac_address.split('-')):
        user_mac_addresses[user_id] = mac_address  # Сохраняем MAC-адрес
        bot.send_message(user_id, f"MAC-адрес успешно сохранён: {mac_address}")
        user_states[user_id] = None  # Очищаем состояние
    else:
        bot.send_message(user_id, "Неверный формат MAC-адреса. Пожалуйста, введите в формате XX-XX-XX-XX-XX-XX.")


# Обработчик для ввода времени будильника пользователем
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'waiting_for_time')
def set_alarm_time(message: Message):
    user_id = message.chat.id
    time_input = message.text.strip()

    # Проверяем, что время введено в правильном формате (HH:MM)
    if len(time_input) == 5 and time_input[2] == ":" and time_input[:2].isdigit() and time_input[3:].isdigit():
        hours, minutes = time_input.split(":")
        hours = int(hours)
        minutes = int(minutes)

        # Проверяем, что введённое время корректно (0 <= hours < 24 и 0 <= minutes < 60)
        if 0 <= hours < 24 and 0 <= minutes < 60:
            user_alarms[user_id] = time_input  # Сохраняем время будильника
            remaining_time = get_remaining_time(time_input)
            bot.send_message(user_id, f"Будильник установлен на {time_input}. Осталось спать: {remaining_time}.")
            user_states[user_id] = None  # Очищаем состояние
        else:
            bot.send_message(user_id,
                             "Время должно быть в пределах 00:00 - 23:59. Пожалуйста, введите корректное время.")
    else:
        bot.send_message(user_id, "Неверный формат времени. Введите время в формате HH:MM (например, 07:30).")


# Функция для получения оставшегося времени до будильника
def get_remaining_time(alarm_time: str) -> str:
    current_time = datetime.now()
    alarm_hour, alarm_minute = map(int, alarm_time.split(":"))
    alarm_time = current_time.replace(hour=alarm_hour, minute=alarm_minute, second=0, microsecond=0)
    if alarm_time < current_time:
        alarm_time += timedelta(days=1)

    time_left = alarm_time - current_time
    hours_left = time_left.seconds // 3600
    minutes_left = (time_left.seconds // 60) % 60
    return f"{hours_left} ч {minutes_left} мин"

# Обработчик всех остальных текстовых сообщений
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) is None)
def default_handler(message: Message):
    bot.send_message(message.chat.id, "Используйте команду /set_alarm для настройки будильника.")


# Запуск бота
bot.polling(none_stop=True)
