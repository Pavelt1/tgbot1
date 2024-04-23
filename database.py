import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

metadata = sq.MetaData()
Base = declarative_base(metadata=metadata)

class Users(Base):
    __tablename__ = "users"
        
    id = sq.Column(sq.BigInteger,primary_key=True)
    name = sq.Column(sq.String(length=40))

    
class Ruswords(Base):
    __tablename__ = "ruswords"

    id = sq.Column(sq.INTEGER,primary_key=True)
    word = sq.Column(sq.String(length=40),unique=True)
    id_users = sq.Column(sq.BigInteger,sq.ForeignKey("users.id"),nullable=False)

    users = relationship(Users,backref="ruswords")


class Engwords(Base):
    __tablename__ = "engwords"

    id = sq.Column(sq.Integer,primary_key=True)
    word = sq.Column(sq.String(length=40),unique=True)
    id_ruwords = sq.Column(sq.Integer,sq.ForeignKey("ruswords.id"),nullable=False)

    ruwords = relationship(Ruswords,backref="engwords")


def create_tables(engine):
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Creating database")