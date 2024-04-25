import sqlalchemy
import random

from database import create_tables, Users, Ruswords, Engwords
from translator import translate_word
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup


DSN = "postgresql://postgres:1996@localhost:5432/test"
engine = sqlalchemy.create_engine(DSN)

Session = sessionmaker(bind=engine)
session = Session()


create_tables(engine)
print('Start telegram bot...')

state_storage = StateMemoryStorage()
token_bot = ""
bot = TeleBot(token_bot, state_storage=state_storage)

switch_add = False
swich_del = False
buttons = []
result = []
        

def session_commit(user):
    session.add(user)
    session.commit()
    session.close()

def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"

def results(id,word):
    global result_word
    if id in result_word:
        result_word[id].append(word)
        if result_word[id].count(word) == 10 and session.query(Ruswords.result).filter(Ruswords.word == word).all() :
            session.query(Ruswords).filter(Ruswords.word == word).update({"result":True})
            session.commit()
            session.close()
    else:
        result_word[id] = [word]


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()

@bot.message_handler(commands=['start'])
def create_cards(message):
    cid = message.chat.id
    user = session.query(Users).filter_by(id = cid).first()
    if not user:
        new_user = Users(id = cid, name = message.from_user.first_name)
        session_commit(new_user)
        bot.send_message(cid, "Привет, незнакомец, давай изучать английский...")
    
    total_count = session.query(func.count(Ruswords.word)).where(Ruswords.id_users == cid).scalar()
    if total_count >= 5:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        global buttons
        buttons = []  
        translate = session.query(Ruswords.word).order_by(func.random()).where(Ruswords.id_users == cid).first() 
        target_word = session.query(Engwords.word).join(Ruswords,Engwords.id_ruwords == Ruswords.id).where(Ruswords.word == translate[0]).first()
        target_word_btn = types.KeyboardButton(target_word[0])
        buttons.append(target_word_btn)
        others = []
        for word in session.query(Engwords.word).order_by(func.random()).where(Engwords.word != target_word[0]).limit(4).all():
            others.append(word[0])
        other_words_btns = [types.KeyboardButton(word) for word in others]
        buttons.extend(other_words_btns)
        random.shuffle(buttons)
        next_btn = types.KeyboardButton(Command.NEXT)
        add_word_btn = types.KeyboardButton(Command.ADD_WORD)
        delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
        buttons.extend([next_btn, add_word_btn, delete_word_btn])
        markup.add(*buttons)

        greeting = f"Выбери перевод слова:\n🇷🇺 {translate[0]}"

        bot.send_message(message.chat.id, greeting, reply_markup=markup)
        bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['target_word'] = target_word[0]
            data['translate_word'] = translate[0]
            data['other_words'] = others

    else:    
        bot.send_message(cid, "У тебя мало слов для изучения. Сохрани несколько и попробуй еще раз.")


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    bot.send_message(message.chat.id, "Продолжаем тренировку.\n")
    create_cards(message)
    


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    global switch_del
    bot.send_message(message.chat.id, "Напишите слово для удаление...")
    switch_del = True

@bot.message_handler(func=lambda message: True and switch_del == True)
def word(message):
    global switch_del
    switch_del = False
    cid = message.chat.id
    text_ru = message.text
    ff = session.query(Ruswords).filter(Ruswords.word == text_ru).first()
    if ff:
        session.query(Engwords).filter(Engwords.word == (translate_word(text_ru).capitalize())).delete()
        session.query(Ruswords).filter(Ruswords.word == text_ru).delete()
        session.commit()
        session.close()
        bot.send_message(cid, "Слово  удалено")
    else:
        bot.send_message(cid, "Слово не найдено")

@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    global switch_add
    bot.send_message(message.chat.id, "Напишите новое слово...")
    switch_add = True

@bot.message_handler(func=lambda message: True and switch_add == True)
def word(message):
    global switch_add
    switch_add = False
    cid = message.chat.id
    text_ru = message.text
    ff = session.query(Ruswords).filter(Ruswords.word == text_ru).first()
    if not ff:
        add_word_r = Ruswords(word = text_ru, id_users = cid)
        session_commit(add_word_r)
        idd = session.query(Ruswords.id).where(Ruswords.word == text_ru).scalar()
        text_en = translate_word(text_ru).capitalize()
        add_word_e = Engwords(word = text_en, id_ruwords = idd)
        session_commit(add_word_e)
        total_count = session.query(func.count(Ruswords.word)).where(Ruswords.id_users == cid).scalar()
        bot.send_message(message.chat.id, f"Слово: {text_ru} успешно добавлено! Его перевод: {text_en} ! Количество слов: {total_count}")
    else:
        bot.send_message(message.chat.id, f"Слово {text_ru} уже есть в БД!")

@bot.message_handler(commands=['info'])
def info(message):
    cid = message.chat.id
    result = ""
    total_count = session.query(func.count(Ruswords.word)).where(Ruswords.id_users == cid).scalar()
    for i in session.query(Ruswords.word).where(Ruswords.id_users == cid).all():
        result += f"{i[0]} "
    bot.send_message(message.chat.id, f"У тебя сохранены следующие слова:\n{result} \nКоличество слов: {total_count}")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    cid = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            hint = show_hint(*hint_text)
            results(cid,text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)
    if session.query(Ruswords.result).filter(Ruswords.word == text).all():
        bot.send_message(message.chat.id, f"Ты молодец! Ты овладел словом {text}! \nТак держать... ")


bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)


