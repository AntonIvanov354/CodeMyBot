import telebot
from telebot import types
import sqlite3
import re

TOKEN = "7948328886:AAFEkbhTT7d-dzc3MeadtnjirLvlefoOjlM"
bot = telebot.TeleBot(TOKEN)    

# Подключаемся к БД
conn = sqlite3.connect("data-set-orders.db", check_same_thread=False)
cursor = conn.cursor()

# Создаём таблицу (если её нет)
cursor.execute("""CREATE TABLE IF NOT EXISTS orders (
    username TEXT,
    order_text TEXT
)""")
conn.commit()

# Функция сохранения заказа
def save_order(username, order_text):
    cursor.execute("INSERT INTO orders (username, order_text) VALUES (?, ?)", (username, order_text))
    conn.commit()

# Функция получения истории заказов
def get_orders(username):
    cursor.execute("SELECT order_text FROM orders WHERE username = ?", (username,))
    orders = cursor.fetchall()
    return [order[0] for order in orders]

# Установка команд
bot.set_my_commands([
    types.BotCommand("start", "Старт"),
    types.BotCommand("order_history", "История заказов"),
    types.BotCommand("new_order", "Новый заказ")
])

# Обработчик команды /start
@bot.message_handler(commands=["start"])
def start_bot(message):
    bot.send_message(message.from_user.id,
                     """👋 Здравствуйте! Этот бот предназначен для оформления заказов.

🔹 Если вы хотите ускорить процесс разработки, подробно опишите, какой бот вам нужен, а также укажите сроки выполнения работы.

📝 Вводить можно только текстом.""")
    keyboard = types.InlineKeyboardMarkup()
    key_yes = types.InlineKeyboardButton(text="📝 Ввести описание заказа", callback_data="yes")
    key_no = types.InlineKeyboardButton(text="📞 Свяжитесь со мной", callback_data="no")
    keyboard.add(key_no, key_yes)
    bot.send_message(message.from_user.id, text="Выберите действие:", reply_markup=keyboard)

# Обработчик callback_query
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "yes":
        bot.send_message(call.message.chat.id, "✏️ Введите описание вашего заказа.")
        bot.edit_message_text("Хорошо", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, task_description_yes)
    elif call.data == "no":
        bot.send_message(call.message.chat.id, "Введите ваш айди, по которому вам можно написать.")
        bot.edit_message_text("Хорошо", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(call.message, task_description_no)

def task_description_no(message):
    username = message.from_user.username
    if username is None:
        bot.send_message(message.from_user.id, "❌ У вас нет username! Установите его в настройках Telegram, чтобы оформлять заказы.")
        return

    order_text = message.text  # Сохраняем введённые параметры
    save_order(username, order_text)  # Сохраняем заказ в БД

    bot.send_message(message.from_user.id, f"✅ Ваш заказ сохранён!")

def task_description_yes(message):
    username = message.from_user.username
    if username is None:
        bot.send_message(message.from_user.id, "❌ У вас нет username! Установите его в настройках Telegram, чтобы оформлять заказы.")
        return

    order_text = message.text  # Сохраняем введённые параметры
    save_order(username, order_text)  # Сохраняем заказ в БД

    bot.send_message(message.from_user.id, "✅ Ваш заказ сохранён!")

# Обработчик команды /order_history
@bot.message_handler(commands=["order_history"])
def order_history(message):
    username = message.from_user.username
    if username is None:
        bot.send_message(message.from_user.id, "❌ У вас нет username! Установите его в настройках Telegram.")
        return

    orders = get_orders(username)  # Получаем заказы из БД по username
    if not orders:
        bot.send_message(message.from_user.id, "📭 У вас пока нет заказов.")
    else:
        # Экранируем спецсимволы для MarkdownV2
        def escape_md(text):
            return re.sub(r'([_*[\]()~>#+-=|{}.!])', r'\\\1', text)

        history_text = "\n\n".join([f"📌 {escape_md(order)}" for order in orders])
        bot.send_message(
            message.from_user.id, 
            f"📜 *История ваших заказов:*\n\n{history_text}", 
            parse_mode="MarkdownV2"
        )

#что будет если ввести команду new order
@bot.message_handler(commands=["new_order"])
def new_order(message):
    txt = "Ваш ответ:"
    bot.send_message(message.from_user.id, "👋 Здравствуйте! Вы захотел оформить новый заказ. Начнем?")
    keyboar = types.InlineKeyboardMarkup()
    key_no = types.InlineKeyboardButton(text="❌ Нет, я нажал случайно!", callback_data="no")
    key_yes = types.InlineKeyboardButton(text="✅ Начнем!", callback_data="yes")
    keyboar.add(key_no, key_yes)
    bot.send_message(message.from_user.id, text = txt, reply_markup=keyboar)

@bot.callback_query_handler(func=lambda call:True)
def new_order_otvet(call):
    if call.data == "no":
        bot.send_message(call.message.chat.id, "Жалко, значит в другой раз 😔")
        return
    elif call.data == "yes":
        bot.send_message(call.message.chat.id, "Отлично. Начнем 🙂")
        start_bot(call.message)

#запуск самого бота
bot.polling(non_stop=True, interval=0)
