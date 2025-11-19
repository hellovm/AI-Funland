import unittest
from backend.app import app

class ApiTests(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    def test_system_info(self):
        r = self.client.get('/api/system/info')
        self.assertEqual(r.status_code, 200)
        j = r.get_json()
        self.assertIn('os', j)
        self.assertIn('python', j)

    def test_models_list(self):
        r = self.client.get('/api/models/list')
        self.assertEqual(r.status_code, 200)
        j = r.get_json()
        self.assertIn('items', j)

if __name__ == '__main__':
    unittest.main()