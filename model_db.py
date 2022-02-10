import logging
from config import SQLALCHEMY_DATABASE_URI
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel('INFO')


class UserInstruments(Base):
    __tablename__ = 'UserInstruments'
    __table_args__ = (
        PrimaryKeyConstraint('userid', 'instrid', 'timestamp'),
    )
    userid = Column(Integer, nullable=False)
    instrid = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(Float, nullable=False)

    def __init__(self, userid=None, instrid=None, price=None, timestamp=None):
        self.userid = userid
        self.instrid = instrid
        self.price = price
        self.timestamp = timestamp

    def __repr__(self):
        return '<UserInstruments %r>' % self.timestamp

    def to_dict(self):
        return {
            'userid': self.userid,
            'instrid': self.instrid,
            'price': self.price,
            'timestamp': self.timestamp
        }


# FUTURE: Tables for UserItemSimilarity & ItemSimilarity for schema checks

if __name__ == '__main__':
    # Configure SQLAlchemy engine
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    # Create database
    Base.metadata.create_all(engine)
    logger.info(f'Database created: {SQLALCHEMY_DATABASE_URI}')
