#!/usr/bin/env python3
""" App's models/classes. """
from heartpsalm import db, bcrypt, login_manager
from flask_login import UserMixin
from datetime import datetime
import uuid
from sqlalchemy import Index


@login_manager.user_loader
def load_user(user_id):
    """
    Loads a user from the database using their unique identifier.

    Returns:
        The user instance of the given user_id, or None if not found.
    """
    return User.query.get(user_id)


class User(db.Model, UserMixin):
    """
    Represents a user with attributes and methods for authentication.
    """
    id = db.Column(
            db.String(36), primary_key=True,
            default=lambda: str(uuid.uuid4())
        )
    username = db.Column(db.String(30), nullable=False)
    email_address = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(60), nullable=False)

    @property
    def password(self):
        """Getter for the password property"""
        return self.password

    @password.setter
    def password(self, text_passwd):
        """Hashes and sets the user's password."""
        self.password_hash = (
                bcrypt.generate_password_hash(text_passwd)
                .decode('utf-8')
            )

    def check_for_correct_paswd(self, inputed_paswd):
        """Validates the provided password against the stored hash."""
        return bcrypt.check_password_hash(self.password_hash, inputed_paswd)


class ChatMessage(db.Model):
    """
    Represents a chat message in the database.
    """
    id = db.Column(db.Integer, primary_key=True)
    # Change this line to match User.id type
    user_id = db.Column(
            db.String(36),
            db.ForeignKey('user.id'),
            nullable=False
        )
    role = db.Column(db.String(1250), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(255), nullable=False)

    user = db.relationship('User', backref=db.backref('messages', lazy=True))
    __table_args__ = (
            Index('idx_chatmessage_timestamp', 'timestamp'),
    )


class ChatConfiguration(db.Model):
    """
    A configuration for chat roles and content.
    """
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(1250))  # Either 'user' or 'assistant'
    content = db.Column(db.Text)  # Store the instructions content

    def __repr__(self):
        """
        Defines the string representation of the ChatConfiguration instance.
        """
        return f'<ChatConfiguration {self.role}>'


def create_default_config():
    """
    Creates default configurations for the user and assistant roles in
    the chat. Checks if any configuration already exists. If not, creates and
    stores default instructions for both user and assistant roles. Adds the
    default user and assistant instructions to the database if not present.
    """
    if not ChatConfiguration.query.first():
        user_instruction = ChatConfiguration(
                role='user',
                content=(
                    "You are an assistant for the HeartPsalm app. "
                    "Your primary goal is to recommend Bible verses to uplift "
                    "the user based on their emotions. Always focus your "
                    "responses on providing spiritual encouragement and "
                    "support through Bible verses. At the end of your "
                    "response, when appropriate, ask if the user would like a "
                    "song to help uplift them. If the user initiates a "
                    "general conversation with inputs like 'hi,' 'hello,' "
                    "'I just want to chat,' 'let's talk,' or similar, "
                    "respond conversationally without inferring emotions. "
                    "If the user explicitly says they want a normal "
                    "conversation, do not analyze emotions or suggest songs. "
                    "Engage conversationally and respectfully."
                    )
                )
        assistant_instruction = ChatConfiguration(
                role='assistant',
                content=(
                    "Hello! How can I assist you today? If you're looking for "
                    "spiritual encouragement, let me know how you're feeling, "
                    "and I'll find some Bible verses for you. "
                    "If you just want to chat, let me know!"
                    )
                )
        db.session.add(user_instruction)
        db.session.add(assistant_instruction)
        db.session.commit()
