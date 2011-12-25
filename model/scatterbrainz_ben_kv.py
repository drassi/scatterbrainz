from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, ForeignKey
from sqlalchemy.databases import postgres
from scatterbrainz.model.meta import metadata
#from scatterbrainz.model import User

Base = declarative_base(metadata=metadata)

class BenKVP(Base):
    __tablename__ = 'scatterbrainz_ben_kv'
    id = Column(u'id', Integer(), primary_key = True)
    key = Column(u'key', Unicode(), nullable = False)
    value = Column(u'value', Unicode(), nullable = False)
    userid = Column(Integer, 
                    ForeignKey('scatterbrainz_user.user_id'), 
                    nullable=True)


    def __init__(self, **kwargs):
        for k,v in kwargs.iteritems():
            self.__setattr__(k,v)
            
