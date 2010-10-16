from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Unicode, DateTime, Boolean, ForeignKey
from scatterbrainz.model.meta import metadata

Base = declarative_base(metadata=metadata)
class Invite(Base):

    __tablename__ = 'invites'

    id = Column(Integer, primary_key=True)
    who = Column(Unicode, nullable=False)
    code = Column(Unicode, nullable=False)
    sent = Column(DateTime, nullable=False)

    def __init__(self, who, code):
        self.who = who
        self.code = code
        self.sent = datetime.now()

    def __repr__(self):
        return "<Invite%s>" % (self.__dict__)

