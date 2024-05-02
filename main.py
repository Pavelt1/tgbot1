import sqlalchemy
import random

from database import create_tables, Users, Words, WordUser
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

buttons = []
result_word = {}
        

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
        if result_word[id].count(word) == 10 :
            session.query(Words).filter(Words.rus == word).update({"result": True})
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
    
    total_count = session.query(func.count(Words.rus)).join(WordUser,Words.id == WordUser.id_word).join(Users,WordUser.id_user == Users.id).where(Users.id == cid).scalar()
    if total_count >= 5:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        global buttons
        buttons = []  
        translate = session.query(Words.rus).join(WordUser,Words.id == WordUser.id_word).join(Users,WordUser.id_user == Users.id).order_by(func.random()).where(Users.id == cid).first() 
        target_word = session.query(Words.eng).where(Words.rus == translate[0]).first()
        target_word_btn = types.KeyboardButton(target_word[0])
        buttons.append(target_word_btn)
        others = []
        for word in session.query(Words.eng).order_by(func.random()).where(Words.eng != target_word[0]).limit(4).all():
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
    bot.send_message(message.chat.id, "Напишите слово для удаление...")
    bot.register_next_step_handler(message, d_word)

def d_word(message):
    cid = message.chat.id
    text = message.text
    id_text = session.query(Words.id).join(WordUser,Words.id == WordUser.id_word).join(Users,WordUser.id_user == Users.id).filter(Words.rus == text and Users.id == cid).first()
    if id_text:
        session.query(WordUser).filter(WordUser.id_word == id_text[0]).delete()
        session.commit()
        session.query(Words).filter(Words.rus == text).delete()
        session.commit()
        session.close()
        bot.send_message(cid, "Слово  удалено")
        info(message)
    else:
        bot.send_message(cid, "Слово не найдено")

@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    bot.send_message(message.chat.id, "Напишите новое слово...")
    bot.register_next_step_handler(message, a_word)

def a_word(message):
    cid = message.chat.id
    text = message.text.capitalize()
    ff = session.query(Words.rus).join(WordUser,Words.id == WordUser.id_word).join(Users,WordUser.id_user == Users.id).filter(Words.rus == text and Users.id == cid).first()
    if not ff:
        add_word = Words(rus = text, eng = translate_word(text).capitalize() )
        session_commit(add_word)
        id_text = session.query(Words.id).where(Words.rus == text).scalar()
        add_worduser = WordUser(id_user = cid, id_word = id_text)
        session_commit(add_worduser)
        total_count = session.query(func.count(Words.rus)).join(WordUser,Words.id == WordUser.id_word).join(Users,WordUser.id_user == Users.id).where(Users.id == cid).scalar()
        bot.send_message(message.chat.id, f"Слово: {text} успешно добавлено! Его перевод: {translate_word(text).capitalize()} ! Количество слов: {total_count}")
    else:
        bot.send_message(message.chat.id, f"Слово {text} уже есть в БД!")

@bot.message_handler(commands=['info'])
def info(message):
    cid = message.chat.id
    result = ""
    total_count = session.query(func.count(Words.rus)).join(WordUser,Words.id == WordUser.id_word).join(Users,WordUser.id_user == Users.id).where(Users.id == cid).scalar()
    for i in session.query(Words.rus).join(WordUser,Words.id == WordUser.id_word).join(Users,WordUser.id_user == Users.id).where(Users.id == cid).all():
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
    bool_res = session.query(Words.result).filter(Words.eng == text).first()
    if bool_res[0]:
        bot.send_message(message.chat.id, f"Ты молодец! Ты овладел словом ! \nТак держать... ")


bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)


