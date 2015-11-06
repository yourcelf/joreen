import json
from django.test import TestCase

from stateparsers import AVAILABLE_STATES, get_searcher

# Create your tests here.
class TestStates(TestCase):
    def test_states(self):
        res = self.client.get('/api/states.json')
        data = json.loads(res.content.decode('utf-8'))
        self.assertEquals(sorted(data['states'].keys()),
                          sorted(AVAILABLE_STATES))
        for abbr, details in data['states'].items():
            self.assertEquals(details['minimum_search_terms'],
                              get_searcher(abbr).minimum_search_terms)
        self.assertEquals(res['Access-Control-Allow-Origin'], '*')

    def options_header(self):
        res = self.client.options('/api/states.json')
        self.assertEquals(res['Access-Control-Allow-Origin'], '*')

class TestSearch(TestCase):
    fixtures = ['facilities']
    def test_inadequate_search_terms(self):
        res = self.client.get('/api/search.json', {
            'state': 'federal', 'first_name': 'John'
        })
        data = json.loads(res.content.decode('utf-8'))
        self.assertEquals(res.status_code, 400)
        self.assertEquals(data['error'], "federal requires one of [['last_name', 'first_name'], ['number']]")

    def test_adequate_search_terms(self):
        res = self.client.get('/api/search.json', {
            'state': 'federal', 'first_name': 'John', 'last_name': 'Smith'
        })
        data = json.loads(res.content.decode('utf-8'))
        self.assertEquals(res.status_code, 200)
        self.assertTrue('error' not in data)
        self.assertEquals(data['errors'], [])
        self.assertTrue(len(data['results']) > 5)
