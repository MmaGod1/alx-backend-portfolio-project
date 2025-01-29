import unittest
from unittest.mock import patch
from flask import session
from heartpsalm import app, db
from heartpsalm.models import User, ChatMessage, ChatConfiguration
from datetime import datetime, timezone


class TestFlaskRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test client and test database"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        db.create_all()

        user_instruction = ChatConfiguration(
                role='user', content='Test user instruction'
            )
        assistant_instruction = ChatConfiguration(
                role='assistant', content='Test assistant instruction'
            )
        db.session.add(user_instruction)
        db.session.add(assistant_instruction)
        db.session.commit()

        self.test_user = User(
                username='testuser', email_address='test@test.com'
            )
        self.test_user.password = 'password123'
        db.session.add(self.test_user)
        db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self):
        """Helper method to log in the test user"""
        return self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
            }, follow_redirects=True)

    def test_home_page_redirect_when_authenticated(self):
        """Test that authenticated users are redirected to chat page"""
        with self.client:
            self.login()
            response = self.client.get('/')
            self.assertEqual(response.status_code, 302)
            self.assertIn('/chat', response.location)

    def test_register_success(self):
        """Test successful user registration"""
        data = {
                'username': 'newuser',
                'email_address': 'newuser@example.com',
                'password1': 'password123',
                'password2': 'password123'
                }
        response = self.client.post(
                '/register', data=data,
                follow_redirects=True
            )
        self.assertEqual(response.status_code, 200)

        user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email_address, 'newuser@example.com')

    def test_login_success(self):
        """Test successful login"""
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You logged in Successfully', response.data)

    def test_home_page_when_not_authenticated(self):
        """Test that non-authenticated users see the home page"""
        with self.client:
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)

            self.assertIn(
                    b'Describe your emotions or how you\'re feeling today.',
                    response.data
                )
            self.assertIn(b'HPLogo.png', response.data)

    def test_chat_page_with_authentication(self):
        """Test chat page access with authenticated user"""
        with self.client:
            self.login()

            with self.client.session_transaction() as sess:
                sess['session_id'] = 'test_session'

            response = self.client.get('/chat')

            self.assertEqual(response.status_code, 200)

            self.assertIn(b'How is testuser feeling', response.data)

            self.assertIn(b'chat-area', response.data)

            self.assertIn(b'input-area', response.data)

            self.assertIn(b'Previous Chats', response.data)

    @patch('heartpsalm.core_functions.detect_sentiment_with_gemini')
    @patch('heartpsalm.core_functions.analyze_intent_with_gemini')
    @patch('heartpsalm.core_functions.generative_ai_response')
    def test_chat_post_message(
            self, mock_ai_response,
            mock_analyze_intent, mock_detect_sentiment
    ):
        """Test posting a message in chat"""
        # Set up mock returns
        mock_detect_sentiment.return_value = "positive"
        mock_analyze_intent.return_value = False
        mock_ai_response.return_value = (
                "I'm doing well, thank you for asking!  "
                "How are you today?\n"
            )

        with self.client:
            self.login()
            with self.client.session_transaction() as sess:
                sess['session_id'] = 'test_session'

            test_user = User.query.filter_by(username='testuser').first()

            message = ChatMessage(
                    user_id=test_user.id,
                    role='user',
                    content='Test message',
                    session_id='test_session',
                    timestamp=datetime.now(timezone.utc)
                    )
            db.session.add(message)
            db.session.commit()

            data = {'user_feeling': 'Hello, how are you?'}
            response = self.client.post('/chat', data=data)
            self.assertEqual(response.status_code, 200)

            response_data = response.get_json()
            response_text = (
                    response_data["assistant_response"]
                    .replace("I am", "I'm")
                    .strip()
                )

            expected_text = (
                    "I'm doing well, thank you for asking!  "
                    "How are you today?"
                )

            self.assertEqual(
                    " ".join(response_text.split()),
                    " ".join(expected_text.split())
                )

    def test_logout(self):
        """Test logout functionality"""
        with self.client:
            self.login()
            response = self.client.get('/logout', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'You have logged out successfully', response.data)

    def test_delete_chat(self):
        """Test chat deletion"""
        with self.client:
            self.login()

            test_user = User.query.filter_by(username='testuser').first()

            message = ChatMessage(
                    user_id=test_user.id,
                    role='user',
                    content='Test message',
                    session_id='test_session',
                    timestamp=datetime.now(timezone.utc)
                    )
            db.session.add(message)
            db.session.commit()

            response = self.client.post(
                    '/delete_chat/test_session', follow_redirects=True
                )
            self.assertEqual(response.status_code, 200)

            messages = ChatMessage.query.filter_by(
                    session_id='test_session'
                ).all()
            self.assertEqual(len(messages), 0)


if __name__ == '__main__':
    unittest.main()
