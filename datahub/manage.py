from flaskext.script import Manager

from datahub.core import app
from datahub.model import db

manager = Manager(app)

@manager.command
def createdb():
    """ Create the SQLAlchemy database. """
    db.create_all()



if __name__ == '__main__':
    manager.run()

