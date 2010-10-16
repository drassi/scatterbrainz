from repoze.what.plugins.quickstart import setup_sql_auth

from scatterbrainz.model.meta import Session
from scatterbrainz.model.auth import User, Group, Permission


def add_auth(app):
    return setup_sql_auth(app, User, Group, Permission, Session,
                          post_login_url='/', post_logout_url='/login')

