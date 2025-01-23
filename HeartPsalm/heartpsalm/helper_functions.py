#!/usr/bin/env python3
""" Helper functions. """
from heartpsalm import db, cache
from flask import session
from heartpsalm.models import ChatMessage
from datetime import datetime
import uuid
import re


def process_message_for_bold_and_paragraphs(text):
    """
    Converts text surrounded by `**` for bold formatting.
    Converts text that spans multiple lines into paragraphs.
    Ignores text that already contains HTML tags to avoid altering them.

    Returns: str: The processed text with bold formatting and paragraph tags.
    """
    if '<' in text and '>' in text:
        return f'<div class="message-content">{text}</div>'

    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = text.replace('*', '')
    text = re.sub(r'([^\n]+)', r'<p>\1</p>', text)

    return text


def generate_session_id():
    """Function to generate session ID"""
    return str(uuid.uuid4())


@cache.memoize(timeout=300)
def load_chat_history(user_id, session_id):
    """
    Fetches chat messages from the database for the given user and session,
        orders them by timestamp, and
        converts the results into a list of dictionaries.
    Uses caching to store the results for 5 minutes to improve performance.

    Returns:
        A list of dictionaries containing the role and
        content of each chat message.
    """
    messages = (
            ChatMessage.query
            .filter_by(user_id=user_id, session_id=session_id)
            .order_by(ChatMessage.timestamp)
            .all()
        )

    chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    return chat_history


def save_chat_history(user_id, session_id, chat_history):
    """
    Saves the chat history to the database for a specific user and session.
    After saving, it invalidates relevant cached data
        to ensure fresh content is loaded next time.

    Args:
        user_id (int): The ID of the user whose chat history is being saved.
        session_id (str): The session ID to associate with the chat history.
        chat_history (list): A list of dictionaries
            containing the role and content of each message.
    """
    for message in chat_history:
        new_message = ChatMessage(
            user_id=user_id,
            role=message["role"],
            content=message["content"],
            timestamp=datetime.utcnow(),
            session_id=session_id
        )
        db.session.add(new_message)
    try:
        db.session.commit()

        cache.delete_memoized(get_chat_files_for_user, user_id)
        cache.delete_memoized(load_chat_history, user_id, session_id)
        cache.delete_memoized(get_chat_preview, user_id, session_id)
    except Exception as e:
        db.session.rollback()
        print(f"Error saving chat history to the database: {e}")


@cache.memoize(timeout=300)
def get_chat_files_for_user(user_id):
    """
    Queries the database to retrieve session IDs for the given user,
        groups them by session ID, and orders them by the most recent message.
    Uses caching to store the results for 5 minutes to improve performance.

    Args:
        user_id (int): The user ID for whom the session files are fetched for.

    Returns:
        A list of session IDs for the user's chat sessions,
            ordered by the most recent message.
    """
    sessions = db.session.query(ChatMessage.session_id) \
        .filter_by(user_id=user_id) \
        .group_by(ChatMessage.session_id) \
        .order_by(db.func.max(ChatMessage.timestamp).desc()) \
        .all()
    return [session[0] for session in sessions]


@cache.memoize(timeout=300)
def get_chat_preview(user_id, session_id):
    """
    Fetches a preview of the first message for a specific user's session.

    Args:
        user_id (int): The user whose session preview is being fetched.
        session_id (str): The session ID for the message preview.

    Returns:
        str: A preview of the first message in the session.
    """
    message = (
            ChatMessage.query
            .filter_by(user_id=user_id, session_id=session_id)
            .order_by(ChatMessage.timestamp)
            .first()
        )
    if message:
        preview = (
                message.content[:30] + "..."
                if len(message.content) > 30
                else message.content
            )
    else:
        preview = "No messages available"
    return preview
