#!/usr/bin/env python3
"""
Telegram Giveaway & Autoposting Bot
===================================
Бот для автопостинга и розыгрышей с обязательной подпиской.
Реализован с использованием библиотеки pyTelegramBotAPI.
"""

import os
import json
import datetime
import threading
import random
from telebot import TeleBot, types

# ================= CONFIG =================

ADMIN_ID = you id (@userinfobot)
TOKEN = 'you bot token (@botfather)'
DB_FILE = 'data/db.txt'

#CONFIG

bot = TeleBot(TOKEN)
admin_conversation = {}
giveaways = {}

#DATABASE

def load_db() -> dict:
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.isfile(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({"channels": []}, f)
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data: dict):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

db = load_db()

#UTILS

def update_participation_button(giveaway_data: dict, message_chat_id: int, message_id: int):
    """Обновляет инлайн-кнопку участия с числом участников."""
    new_count = len(giveaway_data["participants"])
    base_text = giveaway_data.get("base_button_text", "Участвовать")
    new_button_text = f"{base_text} ({new_count})"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(new_button_text, callback_data="participate"))
    try:
        bot.edit_message_reply_markup(message_chat_id, message_id, reply_markup=markup)
    except Exception as e:
        print(f"Ошибка обновления кнопки: {e}")

def get_display_name(user_id: int) -> str:

    try:
        user = bot.get_chat(user_id)
        return "@" + user.username if user.username else str(user.id)
    except Exception:
        return str(user_id)

#HANDLERS

@bot.message_handler(commands=['start'])
def cmd_start(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 Доступ запрещён!")
        return
    text = ("👋 Привет! Добро пожаловать!\n"
            "Команды:\n"
            "  /addchannel – добавить канал\n"
            "  /post – автопостинг\n"
            "  /giveaway – розыгрыш\n"
            "  /stats – статистика")
    bot.reply_to(message, text)

@bot.message_handler(commands=['addchannel'])
def cmd_add_channel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 Доступ запрещён!")
        return
    msg = bot.reply_to(message, "📝 Пришлите ID или @username канала:")
    bot.register_next_step_handler(msg, process_channel)

def process_channel(message):
    channel = message.text.strip()
    if channel not in db.get("channels", []):
        db["channels"].append(channel)
        save_db(db)
        bot.reply_to(message, f"✅ Канал {channel} добавлен!")
    else:
        bot.reply_to(message, f"ℹ️ Канал {channel} уже существует!")

@bot.message_handler(commands=['post'])
def cmd_post(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 Доступ запрещён!")
        return
    admin_conversation['post'] = {}
    msg = bot.reply_to(message, "📝 Введите текст поста:")
    bot.register_next_step_handler(msg, process_post_text)

def process_post_text(message):
    admin_conversation['post']['text'] = message.text
    msg = bot.reply_to(message, "📷 Пришлите картинку или отправьте /skip для пропуска:")
    bot.register_next_step_handler(msg, process_post_image)

def process_post_image(message):
    if message.text == '/skip':
        admin_conversation['post']['image'] = None
    elif message.photo:
        photo = message.photo[-1]
        admin_conversation['post']['image'] = photo.file_id
    else:
        admin_conversation['post']['image'] = None
    msg = bot.reply_to(message, "📢 Введите каналы через запятую (ID или @username):")
    bot.register_next_step_handler(msg, process_post_channels)

def process_post_channels(message):
    channels = [c.strip() for c in message.text.split(',')]
    admin_conversation['post']['channels'] = channels
    msg = bot.reply_to(message, "⏰ Введите время в формате YYYY-MM-DD HH:MM:")
    bot.register_next_step_handler(msg, process_post_time)

def process_post_time(message):
    time_str = message.text.strip()
    try:
        scheduled_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        msg = bot.reply_to(message, "❗ Неверный формат, попробуйте снова:")
        bot.register_next_step_handler(msg, process_post_time)
        return
    admin_conversation['post']['time'] = scheduled_time
    bot.reply_to(message, "✅ Пост запланирован! 😊")
    delay = (scheduled_time - datetime.datetime.now()).total_seconds()
    if delay < 0:
        bot.reply_to(message, "⌛ Время в прошлом, отправляем сразу!")
        delay = 0
    threading.Timer(delay, execute_post, args=(admin_conversation['post'],)).start()

def execute_post(post_data: dict):
    for channel in post_data['channels']:
        try:
            if post_data['image']:
                bot.send_photo(channel, post_data['image'], caption=post_data['text'])
            else:
                bot.send_message(channel, post_data['text'])
        except Exception as e:
            print(f"Ошибка отправки поста в {channel}: {e}")

@bot.message_handler(commands=['giveaway'])
def cmd_giveaway(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 Доступ запрещён!")
        return
    admin_conversation['giveaway'] = {}
    msg = bot.reply_to(message, "🎁 Введите текст розыгрыша:")
    bot.register_next_step_handler(msg, process_giveaway_text)

def process_giveaway_text(message):
    admin_conversation['giveaway']['text'] = message.text
    msg = bot.reply_to(message, "📷 Пришлите фото или отправьте /skip для пропуска:")
    bot.register_next_step_handler(msg, process_giveaway_photo)

def process_giveaway_photo(message):
    if message.text == '/skip':
        admin_conversation['giveaway']['photo'] = None
    elif message.photo:
        photo = message.photo[-1]
        admin_conversation['giveaway']['photo'] = photo.file_id
    else:
        admin_conversation['giveaway']['photo'] = None
    msg = bot.reply_to(message, "🔘 Введите текст кнопки участия:")
    bot.register_next_step_handler(msg, process_giveaway_button)

def process_giveaway_button(message):
    admin_conversation['giveaway']['base_button_text'] = message.text.strip()
    msg = bot.reply_to(message, "🔗 Введите ссылку для получения приза:")
    bot.register_next_step_handler(msg, process_giveaway_claim_link)

def process_giveaway_claim_link(message):
    admin_conversation['giveaway']['claim_link'] = message.text.strip()
    msg = bot.reply_to(message, "🔔 Введите обязательный канал для подписки (ID или @username) или отправьте /skip:")
    bot.register_next_step_handler(msg, process_giveaway_mandatory_channel)

def process_giveaway_mandatory_channel(message):
    text = message.text.strip()
    admin_conversation['giveaway']['mandatory_channel'] = None if text == '/skip' else text
    msg = bot.reply_to(message, "🏆 Введите количество победителей:")
    bot.register_next_step_handler(msg, process_giveaway_num_winners)

def process_giveaway_num_winners(message):
    try:
        num = int(message.text.strip())
    except ValueError:
        msg = bot.reply_to(message, "❗ Введите корректное число:")
        bot.register_next_step_handler(msg, process_giveaway_num_winners)
        return
    admin_conversation['giveaway']['num_winners'] = num
    msg = bot.reply_to(message, "⏰ Введите время подведения итогов (YYYY-MM-DD HH:MM) или количество участников (#10):")
    bot.register_next_step_handler(msg, process_giveaway_deadline_or_count)

def process_giveaway_deadline_or_count(message):
    text = message.text.strip()
    if text.startswith('#'):
        try:
            count = int(text[1:])
            admin_conversation['giveaway']['participant_target'] = count
            admin_conversation['giveaway']['deadline'] = None
        except ValueError:
            msg = bot.reply_to(message, "❗ Неверное значение, попробуйте снова:")
            bot.register_next_step_handler(msg, process_giveaway_deadline_or_count)
            return
    else:
        try:
            deadline = datetime.datetime.strptime(text, "%Y-%m-%d %H:%M")
            admin_conversation['giveaway']['deadline'] = deadline
            admin_conversation['giveaway']['participant_target'] = None
        except ValueError:
            msg = bot.reply_to(message, "❗ Неверный формат времени, попробуйте снова:")
            bot.register_next_step_handler(msg, process_giveaway_deadline_or_count)
            return
    post_giveaway(admin_conversation['giveaway'], message)

def post_giveaway(g_data: dict, message):
    base_text = g_data['base_button_text']
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(f"{base_text} (0)", callback_data="participate")
    markup.add(button)
    channels = db.get("channels", [])
    for channel in channels:
        try:
            if g_data['photo']:
                sent_msg = bot.send_photo(channel, g_data['photo'], caption=g_data['text'], reply_markup=markup)
            else:
                sent_msg = bot.send_message(channel, g_data['text'], reply_markup=markup)
            giveaway_id = f"{channel}_{sent_msg.message_id}"
            giveaways[giveaway_id] = {
                "channel": channel,
                "message_id": sent_msg.message_id,
                "text": g_data['text'],
                "photo": g_data['photo'],
                "base_button_text": base_text,
                "num_winners": g_data['num_winners'],
                "participants": set(),
                "deadline": g_data['deadline'],
                "participant_target": g_data['participant_target'],
                "mandatory_channel": g_data['mandatory_channel'],
                "claim_link": g_data['claim_link']
            }
            if g_data['deadline']:
                delay = (g_data['deadline'] - datetime.datetime.now()).total_seconds()
                if delay < 0:
                    delay = 0
                threading.Timer(delay, conclude_giveaway, args=(giveaway_id,)).start()
        except Exception as e:
            print(f"Ошибка отправки розыгрыша в {channel}: {e}")
    bot.reply_to(message, "🎉 Розыгрыш запущен! Удачи!")

@bot.callback_query_handler(func=lambda call: call.data == "participate")
def callback_participate(call):
    giveaway_id = f"{call.message.chat.id}_{call.message.message_id}"
    if giveaway_id not in giveaways:
        bot.answer_callback_query(call.id, "❗ Розыгрыш не найден или завершён!")
        return
    data = giveaways[giveaway_id]
    user_id = call.from_user.id
    # Проверка обязательной подписки
    if data.get("mandatory_channel"):
        try:
            member = bot.get_chat_member(data["mandatory_channel"], user_id)
            if member.status in ['left', 'kicked']:
                bot.answer_callback_query(call.id, "🚫 Подпишитесь на обязательный канал!")
                return
        except Exception as e:
            print(f"Ошибка проверки подписки: {e}")
            bot.answer_callback_query(call.id, "❗ Не удалось проверить подписку!")
            return
    if user_id in data["participants"]:
        bot.answer_callback_query(call.id, "ℹ️ Вы уже участвуете!")
    else:
        data["participants"].add(user_id)
        update_participation_button(data, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "✅ Вы участвуете!")
        if data.get("participant_target") is not None and len(data["participants"]) >= data["participant_target"]:
            conclude_giveaway(giveaway_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("results_"))
def callback_results(call):
    giveaway_id = call.data.split("_", 1)[1]
    if giveaway_id not in giveaways:
        bot.answer_callback_query(call.id, "❗ Розыгрыш не найден!")
        return
    data = giveaways[giveaway_id]
    winners = data.get("winners", [])
    if not winners:
        bot.answer_callback_query(call.id, "❗ Результаты ещё не готовы!")
        return
    response = "🎉 Победители розыгрыша:\n\n"
    for i, winner in enumerate(winners):
        response += f" - {i+1}. {get_display_name(winner)}\n"
    bot.answer_callback_query(call.id, response, show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("claim_"))
def callback_claim(call):
    giveaway_id = call.data.split("_", 1)[1]
    if giveaway_id not in giveaways:
        bot.answer_callback_query(call.id, "❗ Розыгрыш не найден!")
        return
    data = giveaways[giveaway_id]
    winners = data.get("winners", [])
    if call.from_user.id not in winners:
        bot.answer_callback_query(call.id, "🚫 Вы не победитель!")
        return
    claim_link = data.get("claim_link", "")
    bot.answer_callback_query(call.id, "✅ Поздравляем! Вот ваша ссылка:", url=claim_link)

def conclude_giveaway(giveaway_id: str):
    if giveaway_id not in giveaways:
        return
    data = giveaways[giveaway_id]
    participants = list(data["participants"])
    if not participants:
        try:
            bot.send_message(data["channel"], "😔 Розыгрыш завершён. Участников не найдено.")
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
        del giveaways[giveaway_id]
        return
    if len(participants) < data["num_winners"]:
        winners = participants
    else:
        winners = random.sample(participants, data["num_winners"])
    data["winners"] = winners
    announcement = "🎉 Победители розыгрыша:\n\n" + "\n".join(
        [f" - {i+1}. {get_display_name(w)}" for i, w in enumerate(winners)]
    )
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("Проверить результаты", callback_data=f"results_{giveaway_id}"),
        types.InlineKeyboardButton("Забрать приз", callback_data=f"claim_{giveaway_id}")
    )
    try:
        bot.edit_message_reply_markup(data["channel"], data["message_id"], reply_markup=markup)
    except Exception as e:
        print(f"Ошибка редактирования клавиатуры: {e}")
    try:
        bot.send_message(data["channel"], announcement, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка отправки объявления: {e}")

@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 Доступ запрещён!")
        return
    stats_msg = f"📊 Статистика:\nКаналы: {len(db.get('channels', []))}\nАктивных розыгрышей: {len(giveaways)}"
    bot.reply_to(message, stats_msg)

#STARTER(MAIN)

if __name__ == '__main__':
    print("Bot is running...")
    bot.polling(none_stop=True)

