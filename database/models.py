import sqlalchemy as sq

from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    user_id = sq.Column(sq.Integer, primary_key=True)
    telegram_id = sq.Column(sq.Text, unique=True, nullable=False)
    first_name = sq.Column(sq.Text, nullable=False)


class WordsUsers(Base):
    __tablename__ = 'words_users'

    word_id = sq.Column(sq.Integer, primary_key=True)
    word = sq.Column(sq.Text, unique=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('users.user_id'))
    users = relationship('Users', backref='users')


class GeneralWords(Base):
    __tablename__ = 'general_words'

    pk_word_id = sq.Column(sq.Integer, primary_key=True)
    word = sq.Column(sq.Text, unique=True, nullable=False)


def create_tables(engine):
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
