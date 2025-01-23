#!/usr/bin/env python3
""" Core logic of the app. """
from heartpsalm import app, genai, sp
import random
from heartpsalm.models import ChatMessage


def search_gospel_song(emotion):
    """
    Searches for an uplifting gospel song based on the user's emotion.

    Args:
        emotion (str): The user's emotion.

    Returns:
        str: Song recommendation or error message.
    """
    try:
        query = f"gospel {emotion}"
        results = sp.search(q=query, limit=20, type='track')

        if results['tracks']['items']:
            song = random.choice(results['tracks']['items'])
            song_name = song['name']
            song_artist = song['artists'][0]['name']
            song_url = song['external_urls']['spotify']
            song_recommendation = (
                    f"<div>I found a gospel song for you: "
                    f"<strong>'{song_name}'</strong> by <em>{song_artist}</em>. "
                    f'<a href="{song_url}" target="_blank" class="spotify-btn">'
                    '<i class="fab fa-spotify"></i> Listen on Spotify</a>'
                    "</div>"
                )
            return song_recommendation
        else:
            return "Sorry, I couldn't find a gospel song for that emotion."
    except Exception as e:
        return f"Error searching for a song: {str(e)}"


def generative_ai_response(user_message, chat_history):
    """
    Generates a response from the AI model using
        the user's message and chat history.

    Args:
        user_message (str): The user's input message.
        chat_history (list): A list of past chat messages.

    Returns:
        str: The AI's generated response or an error message.
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        gemini_history = []
        for message in chat_history:
            if isinstance(message, ChatMessage):
                gemini_history.append(
                        {
                            "role": message.role,
                            "parts": [message.content],
                            }
                    )
            elif isinstance(message, dict):
                gemini_history.append(message)
            elif isinstance(message, str):
                gemini_history.append({"role": "user", "parts": [message]})
            else:
                print(f"Type: {type(message)}, value: {message}")
                return "Error: Unexpected message type in chat history."

        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(user_message)

        return response.text

    except Exception as e:
        return f"Error generating response: {str(e)}"


def analyze_intent_with_gemini(user_input):
    """
    Analyzes the user's input to determine if they are asking
        for a song recommendation.
    Uses a generative AI model to classify the input as a song request or not.

    Args:
        user_input (str): The user's input message.

    Returns:
        bool: True if a song recommendation request is implied, else False.
    """
    prompt = (
        "You are a helpful assistant. "
        "Based on the following input, determine if the user is "
        "asking for a song recommendation or inquiring about a specific "
        "song. If the input implies that the user is looking for a song "
        "suggestion, respond with 'yes'. If the user is asking about a "
        "particular song (e.g., asking about a song title or artist), "
        "respond with 'no'. If the user describes the user feelings and "
        "it doesn't implies wanting a song reply with 'no'.\n"
        f"Input: {user_input}\n"
        "Does this input indicate interest in a song recommendation? "
        "Respond with 'yes' or 'no':"
    )

    response_text = generative_ai_response(prompt, chat_history=[])
    if response_text:
        return response_text.lower().strip() == "yes"
    return False


def detect_sentiment_with_gemini(user_input):
    """
    Analyzes user's input sentiment using GeminiAI and maps it to an emotion.

    Args:
        user_input (str): The user's input message.

    Returns:
        str: The detected emotion, such as "joyful," "worship," etc."
    """
    try:
        # GeminiAI's sentiment analyser
        sentiment = gemini_ai.analyze_sentiment(user_input)

        # Map sentiment to emotion
        if sentiment == "positive":
            return "joyful"
        elif sentiment == "neutral":
            return "worship"
        elif sentiment == "negative":
            return "comforting"
        else:
            return "praise"
    except Exception as e:
        return "praise"
