import unittest
import json

from datahub import core
from datahub import model
from datahub import web

JSON = 'application/json'


class ProfileTestCase(unittest.TestCase):

    def setUp(self):
        web.app.config['TESTING'] = True
        web.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        core.db.create_all()
        self.app = web.app.test_client()
        self.make_fixtures()

    def tearDown(self):
        core.db.drop_all()

    def make_fixtures(self):
        # TODO: call logic layer instead, once there is one:
        user = model.User('fixturix')
        core.db.session.add(user)
        core.db.session.commit()

    def test_account_profile_get(self):
        res = self.app.get('/api/v1/profile/no-such-user')
        assert res.status.startswith("404"), res.status

        res = self.app.get('/api/v1/profile/fixturix', 
                headers={'Accept': JSON})
        assert res.status.startswith("200"), res.status
        body = json.loads(res.data)
        assert body['name']=='fixturix', body

    def test_account_profile_put(self):
        res = self.app.get('/api/v1/profile/fixturix', 
                headers={'Accept': JSON})
        body = json.loads(res.data)
        body['name']='fixturix-renamed'
        res = self.app.put('/api/v1/profile/fixturix', 
                data=body, headers={'Accept': JSON})
        body = json.loads(res.data)
        assert body['name']=='fixturix-renamed', body

if __name__ == '__main__':
    unittest.main()
