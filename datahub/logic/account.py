from formencode import Schema, All, validators

from datahub.core import db
from datahub.exc import NotFound
from datahub.model import Account

from datahub.logic.validation import Name, AvailableAccountName

class AccountSchemaState():
    """ Used to let the AvailableAccountName validator know that the 
    current name is taken by the account itself. """

    def __init__(self, current_name):
        self.current_name = current_name

class AccountSchema(Schema):
    allow_extra_fields = True
    name = All(Name(), AvailableAccountName())

def get(name):
    """ Get will try to find an account and return None if no account
    found. Use `find` for an exception-generating variant. """
    return Account.query.filter(Account.name==name).first()

def find(name):
    """ Find an account or yield a `NotFound` exception. """
    account = get(name)
    if account is None:
        raise NotFound('No such account: %s' % name)
    return account

def update(account_name, data):
    """ Update an account's data. """
    account = find(account_name)

    # tell availablename about our current name:
    state = AccountSchemaState(account_name)
    data = AccountSchema().to_python(data, state=state)

    account.name = data['name']
    db.session.commit()
    return account

