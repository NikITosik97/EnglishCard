from database.create_tables import session
from models import GeneralWords

with open('words_for_general_words.txt', 'r', encoding='utf-8') as f:
    words = f.readline().split(',')

    for word in words:
        general_words = GeneralWords(word=word)
        session.add(general_words)
    session.commit()
