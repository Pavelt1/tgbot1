import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

metadata = sq.MetaData()
Base = declarative_base(metadata=metadata)

class Users(Base):
    __tablename__ = "users"
        
    id = sq.Column(sq.BigInteger,primary_key=True)
    name = sq.Column(sq.String(length=40))

    
class Words(Base):
    __tablename__ = "words"

    id = sq.Column(sq.INTEGER,primary_key=True)
    rus = sq.Column(sq.String(length=40))
    eng = sq.Column(sq.String(length=40))
    result = sq.Column(sq.Boolean,default=False)
    

class WordUser(Base):
    __tablename__ = "worduser"

    id = sq.Column(sq.INTEGER,primary_key=True)
    id_user = sq.Column(sq.BigInteger,sq.ForeignKey("users.id"),nullable=False)
    id_word = sq.Column(sq.Integer,sq.ForeignKey("words.id"),nullable=False)

    words = relationship(Words,backref="worduser")
    users = relationship(Users,backref="worduser")


def create_tables(engine):
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Creating database")
