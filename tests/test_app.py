import unittest
from main import app


class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        """Set up test client."""
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_home_page(self):
        """Test if the home page loads correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Chatbot", response.data)

    def test_chat_endpoint(self):
        """Test the chat endpoint with a sample message."""
        response = self.client.post('/chat', json={"message": "How are you?"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"reply", response.data)

    def test_empty_data(self):
        """Test the chat endpoint with empty data."""
        response = self.client.post('/chat', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Message is required", response.data)


if __name__ == "__main__":
    unittest.main()
