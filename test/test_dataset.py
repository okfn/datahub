import unittest
import json

from datahub import core
from datahub import model
from datahub import web

JSON = 'application/json'

DATASET_FIXTURE = {'name': 'world', 
                    'summary': 'A list of everything!'}

from test_resource import RESOURCE_FIXTURE
from util import make_test_app, tear_down_test_app
from util import create_fixture_user, AUTHZ

class DatasetTestCase(unittest.TestCase):

    def setUp(self):
        self.app = make_test_app()
        self.make_fixtures()

    def tearDown(self):
        tear_down_test_app()

    def make_fixtures(self):
        create_fixture_user(self.app)
        self.app.post('/api/v1/dataset/fixture', 
                headers={'Authorization': AUTHZ},
                data=DATASET_FIXTURE)

    def test_user_dataset_index(self):
        res = self.app.get('/api/v1/dataset/fixture')
        body = json.loads(res.data)
        assert len(body)==1, body

    def test_user_dataset_create_as_json(self):
        data = json.dumps({'name': 'foo',
                           'summary': 'A foo'})
        res = self.app.post('/api/v1/dataset/fixture', data=data, 
                headers={'Accept': JSON, 'Authorization': AUTHZ}, 
                content_type=JSON,
                follow_redirects=True)
        body = json.loads(res.data)
        assert isinstance(body, dict)

    def test_user_dataset_create_as_form_data(self):
        data = {'name': 'foo',
                'summary': 'A foo'}
        res = self.app.post('/api/v1/dataset/fixture', data=data, 
                headers={'Accept': JSON, 'Authorization': AUTHZ}, 
                follow_redirects=True)
        body = json.loads(res.data)
        assert isinstance(body, dict)
        assert body['name']=='foo', body
    
    def test_user_dataset_create_no_authz(self):
        data = {'name': 'foo',
                'summary': 'A foo'}
        res = self.app.post('/api/v1/dataset/fixture', data=data, 
                headers={'Accept': JSON}, follow_redirects=True)
        assert res.status.startswith("403"), res.status

    def test_dataset_get(self):
        res = self.app.get('/api/v1/dataset/fixture/world')
        body = json.loads(res.data)
        assert body['name']=='world', body
        assert 'created_at' in body, body
        assert 'updated_at' in body, body

    def test_nonexistent_resource_get(self):
        res = self.app.get('/api/v1/dataset/fixture/no-such-dataset')
        assert res.status.startswith("404"), res.status
        assert 'HTML' in res.data, res.data 

    def test_nonexistent_dataset_get_as_json(self):
        res = self.app.get('/api/v1/dataset/fixture/no-such-dataset',
                headers={'Accept': JSON})
        assert res.status.startswith("404"), res.status
        body = json.loads(res.data)
        assert 'status' in body, body

    def test_dataset_update(self):
        data = DATASET_FIXTURE.copy() 
        data['name'] = 'mars'
        res = self.app.put('/api/v1/dataset/fixture/no-world',
                           headers={'Authorization': AUTHZ},
                           data=data)
        assert res.status.startswith("404"), res.data

        res = self.app.put('/api/v1/dataset/fixture/world',
                           data=data)
        assert res.status.startswith("403"), res.data

        res = self.app.put('/api/v1/dataset/fixture/world',
                           headers={'Authorization': AUTHZ},
                           data=data)
        res = self.app.get('/api/v1/dataset/fixture/mars')
        body = json.loads(res.data)
        assert body['name']=='mars', body

    def test_dataset_delete(self):
        res = self.app.delete('/api/v1/dataset/fixture/no-world',
                              headers={'Authorization': AUTHZ})
        assert res.status.startswith("404"), res.data
        
        res = self.app.delete('/api/v1/dataset/fixture/world')
        assert res.status.startswith("403"), res.data

        res = self.app.delete('/api/v1/dataset/fixture/world',
                              headers={'Authorization': AUTHZ})
        assert res.status.startswith("410"), res.data

        res = self.app.get('/api/v1/dataset/fixture/world')
        assert res.status.startswith("404"), res.data

    def test_create_invalid_data(self):
        data = DATASET_FIXTURE.copy() 
        data['name'] = 'invalid name'
        res = self.app.post('/api/v1/dataset/fixture', data=data, 
                            headers={'Accept': JSON, 'Authorization': AUTHZ})
        assert res.status.startswith("400"), res
        data = json.loads(res.data)
        assert 'name' in data['errors'], data

    def test_create_missing_data(self):
        data = DATASET_FIXTURE.copy() 
        data['name'] = ''
        res = self.app.post('/api/v1/dataset/fixture', data=data, 
                            headers={'Accept': JSON, 'Authorization': AUTHZ})
        assert res.status.startswith("400"), res
        data = json.loads(res.data)
        assert 'name' in data['errors'], data

    def test_create_existing_name(self):
        res = self.app.post('/api/v1/dataset/fixture', 
                            data=DATASET_FIXTURE, 
                            headers={'Accept': JSON, 'Authorization': AUTHZ})
        assert res.status.startswith("400"), res
        data = json.loads(res.data)
        assert 'name' in data['errors'], data

    def test_create_with_meta(self):
        data = DATASET_FIXTURE.copy() 
        data['name'] = 'meta-world'
        data['meta'] = {'non_schema': 'hooray'}
        res = self.app.post('/api/v1/dataset/fixture', 
                            data=json.dumps(data), 
                            content_type=JSON,
                            follow_redirects=True,
                            headers={'Accept': JSON, 
                                     'Authorization': AUTHZ})
        assert res.status.startswith("200"), res
        data = json.loads(res.data)
        assert 'hooray'==data['meta']['non_schema'], data

    def test_create_with_meta_invalid_key(self):
        data = RESOURCE_FIXTURE.copy() 
        data['name'] = 'meta-world'
        data['meta'] = {'non schema': 'hooray'}
        res = self.app.post('/api/v1/dataset/fixture', 
                            data=json.dumps(data), 
                            content_type=JSON,
                            headers={'Accept': JSON,
                                     'Authorization': AUTHZ})
        assert res.status.startswith("400"), res
        data = json.loads(res.data)
        assert 'meta' in data['errors'], data

    def test_add_resource_to_dataset(self):
        res = self.app.post('/api/v1/resource/fixture',
                            data=RESOURCE_FIXTURE, 
                            headers={'Accept': JSON, 'Authorization': AUTHZ})

        data = {'owner': 'fixture',
                'name': RESOURCE_FIXTURE['name']}
        res = self.app.post('/api/v1/dataset/fixture/world/resources',
                            data=data,
                            headers={'Accept': JSON, 'Authorization': AUTHZ})
        assert res.status.startswith("302"), res

        res = self.app.post('/api/v1/dataset/fixture/no-ds/resources',
                            data=data,
                            headers={'Accept': JSON, 'Authorization': AUTHZ})
        assert res.status.startswith("404"), res

        res = self.app.get('/api/v1/dataset/fixture/world/resources',
                            data=data,
                            headers={'Accept': JSON})
        assert res.status.startswith("200"), res
        body = json.loads(res.data)
        assert len(body)==1, body
        assert body[0]['name']==data['name'], body
        assert body[0]['owner']==data['owner'], body

    def test_add_non_existing_resource_to_dataset(self):
        res = self.app.post('/api/v1/resource/fixture',
                            data=RESOURCE_FIXTURE, 
                            headers={'Accept': JSON, 'Authorization': AUTHZ})

        data = {'owner': 'fixture'}
        res = self.app.post('/api/v1/dataset/fixture/world/resources',
                            data=data,
                            headers={'Accept': JSON, 'Authorization': AUTHZ})
        assert res.status.startswith("400"), res

        data = {'owner': 'fixture',
                'name': 'does-not-exist'}
        res = self.app.post('/api/v1/dataset/fixture/world/resources',
                            data=data,
                            headers={'Accept': JSON, 'Authorization': AUTHZ})
        assert res.status.startswith("404"), res

    def test_remove_resource_from_dataset(self):
        res = self.app.post('/api/v1/resource/fixture',
                            data=RESOURCE_FIXTURE, 
                            headers={'Accept': JSON, 'Authorization': AUTHZ})

        data = {'owner': 'fixture',
                'name': RESOURCE_FIXTURE['name']}
        res = self.app.post('/api/v1/dataset/fixture/world/resources',
                            data=data,
                            headers={'Accept': JSON, 'Authorization': AUTHZ})
        res = self.app.get('/api/v1/dataset/fixture/world/resources',
                            data=data,
                            headers={'Accept': JSON})
        body = json.loads(res.data)
        assert len(body)==1, body
        u = '/api/v1/dataset/fixture/world/resources/fixture/%s'
        res = self.app.delete(u % RESOURCE_FIXTURE['name'],
                            data=data,
                            headers={'Accept': JSON, 'Authorization': AUTHZ})
        res = self.app.get('/api/v1/dataset/fixture/world/resources',
                            data=data,
                            headers={'Accept': JSON,})
        body = json.loads(res.data)
        assert len(body)==0, body

    def test_user_resource_create_in_wui(self):
        data = {'name': 'mars', 'summary': 'A foo'}
        res = self.app.post('/dataset', data=data, 
                headers={'Authorization': AUTHZ},
                follow_redirects=True)
        assert 'A foo' in res.data, res.data

    def test_user_dataset_create_in_wui_with_resource(self):
        self.app.post('/api/v1/resource/fixture', 
                headers={'Authorization': AUTHZ},
                data=RESOURCE_FIXTURE)
        data = {'name': 'mars',
                'summary': 'A foo', 'resource.owner': 'fixture', 
                'resource.name': RESOURCE_FIXTURE['name']}
        res = self.app.post('/dataset', data=data, 
                headers={'Authorization': AUTHZ})
        assert 'fixture/my-file' in res.headers.get('Location'), res.headers

    def test_wui_dataset_get(self):
            res = self.app.get('/fixture/world')
            assert res.status.startswith("200"), res.status
            assert 'A list of everything' in res.data, res.data



if __name__ == '__main__':
    unittest.main()


