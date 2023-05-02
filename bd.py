import sqlalchemy as sq
from sqlalchemy import PrimaryKeyConstraint, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

Base = declarative_base()

class Seen_persones(Base):
    __tablename__ = 'seen_persones'
    __table_args__ = (PrimaryKeyConstraint('seen_person_id', 'client_id_client', name='pk'),)


    seen_person_id = sq.Column(sq.Integer, sq.ForeignKey("person.person_id"))
    client_id_client = sq.Column(sq.Integer, sq.ForeignKey("client.client_id"))
    liked = sq.Column(sq.Boolean, default=False)


class Client(Base):
    __tablename__ = 'client'

    client_id = sq.Column(sq.Integer, primary_key=True)
    first_name = sq.Column(sq.Text)
    bdate = sq.Column(sq.Date)
    sex = sq.Column(sq.Integer)
    city = sq.Column(sq.Integer)
    age = sq.Column(sq.Integer)
    person = relationship(Seen_persones, backref='user')

    def __str__(self):
        return f"{self.client_id}, {self.first_name}, {self.bdate}, {self.city}, {self.city}"


class Person(Base):
    __tablename__ = 'person'

    person_id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.Text)
    bdate = sq.Column(sq.Date)
    sex = sq.Column(sq.Integer)
    city = sq.Column(sq.Integer)
    client = relationship(Seen_persones, backref="person")

    def __str__(self):
        return f"{self.person_id}, {self.name}, {self.bdate}, {self.sex}, {self.city}"


def create_tables(engine):
    Base.metadata.create_all(engine)

engine = create_engine('postgresql://postgres:Anast29123@localhost:5432/VKinder')
create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()
session.close()
