import requests

from string import punctuation
from database.models import Users, WordsUsers, GeneralWords
from database.create_tables import session
from telebot import TeleBot, types
from config import TOKEN, YANDEX_TOKEN
from random import choice
from bs4 import BeautifulSoup

POSITION: int = 0
START: int = 0

bot = TeleBot(TOKEN)
user_state = {}


@bot.message_handler(commands=['start'])
def bot_send_message(message: types.Message):
    """
    Processes the start command.
    Checks if the user is in the database, if so, launches the menu, otherwise enters the user into the database
    and assigns him 10 common words.
    :param message:
    :return:
    """
    availability_user: list[tuple] = session.query(Users.telegram_id).filter(
        Users.telegram_id == str(message.from_user.id)).all()
    if len(availability_user) < 1:
        general_words: list[str] = [word[0] for word in session.query(GeneralWords.word).all()]
        session.add(Users(telegram_id=message.from_user.id, first_name=message.from_user.first_name))
        session.commit()
        pk_user: int = session.query(Users.user_id).filter(Users.telegram_id == str(message.from_user.id)).all()[0][0]
        for word_ in general_words:
            session.add(WordsUsers(word=word_, user_id=pk_user))
            session.commit()
    global START
    START = 1
    menu(message)


@bot.message_handler(content_types=['text'])
def menu(message: types.Message):
    """
    Creates 4 menu buttons and saves position 1(menu).
    :param message:
    :return:
    """
    global POSITION
    POSITION = 1
    markup = types.ReplyKeyboardMarkup()
    start = types.KeyboardButton(text='▶️ Начать')
    statistics = types.KeyboardButton(text='📈 Статистика')
    add_word = types.KeyboardButton(text='➕ Добавить слово')
    del_word_ = types.KeyboardButton(text='❌ Удалить слово')
    markup.row(start, statistics)
    markup.row(add_word, del_word_)
    bot.send_message(message.chat.id, text='⬇️ Выберите пункт меню!', reply_markup=markup)
    bot.register_next_step_handler(message, handler_all_message)


@bot.message_handler(content_types=['text'])
def process_bot(message: types.Message):
    """
    Creates a list of 4 random words from the user's database, translates the list of Russian words into English
    and creates a dictionary, also takes a random word and a generated list.
    5 buttons and asks the user to translate the word into English
    :param message:
    :return:
    """
    global POSITION
    POSITION = 2
    list_words_ru: list[str] = choose_random_words(message)
    result_words: dict = translate_words_ru_en(list_words_ru)
    if 'ego' in result_words:
        result_words['i'] = result_words.pop('ego')
    send_random_word: str = choice(list_words_ru)
    markup = types.ReplyKeyboardMarkup()
    button1 = types.KeyboardButton(text=f'{"".join([key for key in result_words.keys()][0]).capitalize()}')
    button2 = types.KeyboardButton(text=f'{"".join([key for key in result_words.keys()][1]).capitalize()}')
    button3 = types.KeyboardButton(text=f'{"".join([key for key in result_words.keys()][2]).capitalize()}')
    button4 = types.KeyboardButton(text=f'{"".join([key for key in result_words.keys()][3]).capitalize()}')
    button5 = types.KeyboardButton(text='🔙 Назад')
    markup.row(button1, button2)
    markup.row(button3, button4)
    markup.row(button5)

    bot.send_message(message.chat.id, text=f'Переведи слово ➡️ {send_random_word}',
                     reply_markup=markup)

    bot.register_next_step_handler(message, check_valid_word,
                                   send_random_word=send_random_word,
                                   list_words_ru=list_words_ru,
                                   result_words=result_words)


def choose_random_words(message: types.Message) -> list[str]:
    """
    The function returns a list of 4 random words of the user
    """

    pk_user: int = session.query(Users.user_id).filter(Users.telegram_id == str(message.from_user.id)).all()[0][0]
    pk_word: list = [pk[0] for pk in session.query(WordsUsers.word_id).filter(WordsUsers.user_id == pk_user).all()]

    pk_words: list[int] = []
    while len(pk_words) != 4:
        pk: int = choice(pk_word)
        if pk not in pk_words:
            pk_words.append(pk)

    list_random_words: list[str] = []
    for num in pk_words:
        list_random_words.append(session.query(WordsUsers.word).filter(WordsUsers.word_id == num
                                                                       and WordsUsers.user_id == pk_user).all()[0][0])

    return list_random_words


def translate_words_ru_en(lst_words: list[str]) -> dict:
    """
    The function translates a Russian word into English and returns a dictionary,
    if there is no such word, returns False
    :param lst_words:
    :return:
    """
    result_dict: dict = {}
    for word in lst_words:
        params = {'key': YANDEX_TOKEN,
                  'lang': 'ru-en',
                  'text': word}
        response = requests.get(url='https://dictionary.yandex.net/api/v1/dicservice.json/lookup', params=params).json()

        try:
            result_dict.setdefault(response['def'][0]['tr'][0]['text'], word)
        except IndexError:
            return False

    return result_dict


def translate_words_en_ru(lst_words: list[str]) -> list[str]:
    """
    The function translates an English word into Russian and returns a list of all its synonyms.
    :param lst_words:
    :return:
    """
    for word in lst_words:
        params = {'key': YANDEX_TOKEN,
                  'lang': 'en-ru',
                  'text': word}
        response = requests.get(url='https://dictionary.yandex.net/api/v1/dicservice/lookup', params=params).text

        soup = BeautifulSoup(response, 'xml')
        tag = soup.find_all('text')
        all_transfers: list[str] = [translation.text for translation in tag]

        return all_transfers


def check_valid_word(message: types.Message, *args, **kwargs):
    """
    The function checks whether the word sent by the user is in the resulting dictionary
    and whether the word sent by the program is in the word lists for buttons.
    :param message:
    :param args:
    :param kwargs:
    :return:
    """
    if (message.text.lower().strip(punctuation) in kwargs['result_words'] and kwargs['send_random_word'] in
            kwargs['list_words_ru']):
        all_transfers: list[str] = translate_words_en_ru([message.text.strip(punctuation)])
        if kwargs['send_random_word'].lower() in all_transfers:
            bot.send_message(message.chat.id, text='✅ Ты ответил верно!')
            process_bot(message)
        else:
            bot.send_message(message.chat.id, text='❌ Попробуй еще!')
            process_bot(message)
    else:
        handler_all_message(message)


def add_new_word(message: types.Message):
    """
    the function adds a new user word to the database.
    :param message:
    :return:
    """
    if message.text in punctuation:
        bot.send_message(message.chat.id, text='🤷 Нет такого слова!')
        menu(message)
    else:
        check_word = session.query(WordsUsers.word).filter(
            WordsUsers.word == message.text.capitalize().strip(punctuation)).all()
        if len(check_word) > 1:
            bot.send_message(message.chat.id, text='⚠️ Слово уже есть в твоем списке!')
            menu(message)

        elif translate_words_ru_en([message.text.strip(punctuation)]):
            user_id = session.query(Users.user_id).filter(Users.telegram_id == str(message.from_user.id))

            session.add(WordsUsers(word=message.text.capitalize().strip(punctuation), user_id=user_id))
            session.commit()
            bot.send_message(message.chat.id, text='✅ Слово успешно добавлено!')
            get_statistics(message)
            menu(message)

        else:
            bot.send_message(message.chat.id, text='🤷 Нет такого слова!')
            menu(message)


def del_word(message: types.Message):
    """
    The function removes a word from the database.
    :param message:
    :return:
    """
    user_id = session.query(Users.user_id).filter(Users.telegram_id == str(message.from_user.id))
    try:
        del_id_word_ = \
            session.query(WordsUsers.word_id).filter(
                WordsUsers.word == message.text.capitalize().strip(punctuation)).one()[
                0]

        session.query(WordsUsers).filter(WordsUsers.word_id == del_id_word_
                                         and WordsUsers.user_id == user_id).delete()
        session.commit()
        bot.send_message(message.chat.id, text='✅ Слово успешно удалено!')
        get_statistics(message)
        menu(message)
    except Exception:
        bot.send_message(message.chat.id, text='⚠️ Такого слова нет в твоем списке!')
        menu(message)


def get_statistics(message: types.Message):
    """
    The function displays user statistics. The number of words studied and the words themselves.
    :param message:
    :return:
    """
    user_id = session.query(Users.user_id).filter(Users.telegram_id == str(message.from_user.id))
    count_word_user: int = len(session.query(WordsUsers.word_id).filter(WordsUsers.user_id == user_id).all())
    if count_word_user >= 4:
        global START
        START = 1
    else:
        START = 0
    words_user = [word[0] + '\n' for word in session.query(WordsUsers.word).filter(WordsUsers.user_id == user_id).all()]
    markup = types.ReplyKeyboardMarkup()
    back = types.KeyboardButton(text='🔙 Назад')
    markup.add(back)
    if count_word_user > 0:
        bot.send_message(message.chat.id, text=f'Количество слов ➡️ {count_word_user} ☺️:\n'
                                               f'{"➖" * 10}\n'
                                               f'{"".join([word for word in words_user])}', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, text='Список пустой! 😔')


def handler_all_message(message: types.Message):
    """
    Handler for all events.
    :param message:
    :return:
    """
    user_state[message.chat.id] = message.text

    if user_state[message.chat.id] == '▶️ Начать':
        global START
        get_statistics(message)
        if START == 1:
            process_bot(message)
        else:
            bot.send_message(message.chat.id, text='⚠️ У тебя должно быть минимум 4 слова.\nДобавьте слова!')
            menu(message)

    elif user_state[message.chat.id] == '📈 Статистика':
        get_statistics(message)

    elif user_state[message.chat.id] == '🔙 Назад':
        menu(message)

    elif user_state[message.chat.id] == '➕ Добавить слово':
        bot.send_message(message.chat.id, text='⌨️ Напиши слово которое хочешь изучать!\nНа Русском языке 🇷🇺', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, add_new_word)

    elif user_state[message.chat.id] == '❌ Удалить слово':
        bot.send_message(message.chat.id, text='⌨️ Напиши слово которое хочешь удалить!\nНа Русском языке 🇷🇺', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, del_word)
    else:
        if POSITION == 1:
            bot.send_message(message.chat.id, text='⚠️ Такого варианта меню нет!')
            menu(message)
        else:
            bot.send_message(message.chat.id, text='⚠️ Такого варианта ответа нет!')
            process_bot(message)


if __name__ == '__main__':
    bot.polling(none_stop=True)
