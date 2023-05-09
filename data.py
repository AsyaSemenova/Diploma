import sqlalchemy as sq
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Client(Base):
    __tablename__ = 'Client'

    user_id = sq.Column(sq.Integer, primary_key=True)
    id = sq.Column(sq.Integer, unique=True)

    def __str__(self):
        return f'Client {self.id}: {self.user_id}'


class Person(Base):

    __tablename__ = 'Person'

    user_id = sq.Column(sq.Integer, primary_key=True)
    id = sq.Column(sq.Integer, unique=True)

    def __str__(self):
        return f'Person {self.id}: {self.user_id}'


class seen_person(Base):

    __tablename__ = 'seen_person'

    user_id = sq.Column(sq.Integer, primary_key=True)
    id = sq.Column(sq.Integer, unique=True)
    first_name = sq.Column(sq.String)
    last_name = sq.Column(sq.String)
    vk_link = sq.Column(sq.String, unique=True)

    def __str__(self):
        return f'Seen person {self.id}: {self.user_id}, {self.first_name},{self.last_name}, {self.vk_link},'


def create_tables(engine):
    Base.metadata.create_all(engine)


def drop_tables(engine):
    Base.metadata.drop_all(engine)

