"""Setup the scatterbrainz application"""
import logging

from datetime import datetime

from scatterbrainz.config.environment import load_environment
from scatterbrainz.model import meta
from scatterbrainz.model.meta import Session
from scatterbrainz.model import User, Group, Permission

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup scatterbrainz here"""
    load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    log.info("Creating tables")
    meta.metadata.create_all(bind=meta.engine)
    log.info("Tables created")
    
    session = Session()
    session.begin()
    
    loginPerm = Permission()
    loginPerm.permission_name = u'login'
    
    adminPerm = Permission()
    adminPerm.permission_name = u'admin'
    
    adminGroup = Group()
    adminGroup.group_name = u'admins'
    adminGroup.permissions = [loginPerm, adminPerm]
    
    userGroup = Group()
    userGroup.group_name = u'users'
    userGroup.permissions = [loginPerm]
    
    admin = User()
    admin.user_name = u'admin'
    admin.password = u'default'
    admin.who = u'admin'
    admin.registered = datetime.now()
    admin.groups = [adminGroup]
    
    session.add_all([loginPerm, adminPerm, adminGroup, userGroup, admin])
    
    session.commit()
    
