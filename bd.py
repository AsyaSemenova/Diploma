import sqlalchemy as sq
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

Base = declarative_base()
db = "postgresql://postgres:postgres@localhost:5432/VKinder"
engine = sq.create_engine(db)


class seen_persones(Base):
    __tablename__ = 'seen_persones'
    __table_args__ = (PrimaryKeyConstraint('seen_person_id', 'user_id_user', name = 'pk'),)


    seen_person_id = sq.Column(sq.Integer, sq.ForeignKey("person.person_id"))
    user_id_user = sq.Column(sq.Integer, sq.ForeignKey("user.user_id"))
    liked = sq.Column(sq.Boolean, default=False)


class client(Base):
    __tablename__ = 'client'

    user_id = sq.Column(sq.Integer, primary_key=True)
    first_name = sq.Column(sq.String(length=40))
    bdate = sq.Column(sq.String)
    sex = sq.Column(sq.Integer)
    city = sq.Column(sq.Integer)
    age = sq.Column(sq.Integer)
    person = relationship(seen_persones, backref='user')

    def __str__(self):
        return f"{self.user_id}, {self.first_name}, {self.bdate}, {self.city}, {self.city}"


class person(Base):
    __tablename__ = 'person'

    person_id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String(length=40))
    bdate = sq.Column(sq.String)
    sex = sq.Column(sq.Integer)
    city = sq.Column(sq.Integer)
    user = relationship(seen_persones, backref="person")

    def __str__(self):
        return f"{self.person_id}, {self.name}, {self.bdate}, {self.sex}, {self.city}"


def create_tables(engine):
    Base.metadata.create_all(engine)


create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()

session.close()