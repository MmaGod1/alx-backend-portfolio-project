#!/usr/bin/env python3
""" Routes to differnt functionalites. """
from heartpsalm import app, db, cache
from heartpsalm.models import User, ChatMessage, ChatConfiguration
from heartpsalm.forms import RegisterForm, LoginForm
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from flask import (
        render_template,
        request, redirect,
        url_for, flash,
        session, jsonify)
from heartpsalm.core_functions import (
        search_gospel_song,
        generative_ai_response,
        detect_sentiment_with_gemini,
        analyze_intent_with_gemini)

from heartpsalm.helper_functions import (
        process_message_for_bold_and_paragraphs,
        generate_session_id, load_chat_history,
        save_chat_history, get_chat_files_for_user,
        get_chat_preview)


@app.context_processor
def utility_functions():
    """
    Registers `get_chat_preview` as a global template function.
    Returns:
        dict: Maps `get_chat_preview` to be used in templates.
    """
    return dict(get_chat_preview=get_chat_preview)


@app.route("/")
@app.route("/home")
def home_page():
    """
    Renders the home page.

    Returns:
        Redirects to the chat page if the user is authenticated/logged in,
        otherwise renders the home page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('chat_page'))
    return render_template("home.html")


@app.route('/register', methods=["GET", "POST"])
def register_page():
    """
    Handles the user registration process.

    Returns:
        Response: Redirects to the chat page on successful registration,
        otherwise flashes error messages.
    """
    form = RegisterForm()
    if form.validate_on_submit():
        create_user = User(
                username=form.username.data,
                email_address=form.email_address.data,
                password=form.password1.data
                )
        db.session.add(create_user)
        db.session.commit()

        login_user(create_user)
        flash(
                f"Account created successfully! "
                f"You are now logged in as: {create_user.username}",
                category='success'
            )

        return redirect(url_for("chat_page"))

    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(
                    f"There was an error creating a user: {err_msg}",
                    category="danger"
                )

    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """
    Handles user login process.
    Validates the submitted credentials and logs the user in if valid.

    Returns:
        Response: Redirects to the chat page on successful login,
        otherwise flashes error messages.
    """
    form = LoginForm()
    if form.validate_on_submit():
        inputed_username = (
                User.query
                .filter_by(username=form.username.data)
                .first()
            )

        if inputed_username and inputed_username.check_for_correct_paswd(
                inputed_paswd=form.password.data
                ):
            login_user(inputed_username)

            # Clear any existing session ID when logging in
            session.pop('session_id', None)

            flash(
                    f'You logged in Successfully as: '
                    f'{inputed_username.username}',
                    category='success'
                )

            return redirect(url_for('chat_page'))
        else:
            flash(
                    'Username and password did not match! Please try again.',
                    category='danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout_page():
    """
    Logs the user out and redirects to the home page.

    Returns:
        Redirects to the home page after logging out.
    """
    logout_user()
    flash('You have logged out successfully!', category='info')
    return redirect(url_for('home_page'))


@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat_page():
    """
    Handles the chat page. Fetches chat history and instructions from the
        database, processes user input, and provides a response from the
        assistant based on detected emotion and intent.

    Returns:
        Renders the chat page with the history and instructions, a
        JSON response with user input and assistant response for POST requests.
    """
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()

    # fetch chat history from the database
    chat_history_query = ChatMessage.query.filter_by(
            user_id=current_user.id,
            session_id=session['session_id']
            ).order_by(ChatMessage.timestamp).all()

    chat_history = [
            {"role": msg.role,
             "content": process_message_for_bold_and_paragraphs(msg.content)}
            for msg in chat_history_query
        ]

    # load instructions from the database
    user_instruction = ChatConfiguration.query.filter_by(role='user').first()

    assistant_instruction = (
            ChatConfiguration.query
            .filter_by(role='assistant')
            .first()
        )

    if not user_instruction or not assistant_instruction:
        flash(
                "Chat configuration not found. "
                "Please contact an administrator.",
                "error"
            )

        return render_template("chat.html", history=chat_history)

    if request.method == "POST":
        user_input = request.form.get("user_feeling", "").strip()
        if not user_input:
            return jsonify({"error": "Message cannot be empty"}), 400

        # save user message to the database
        user_message = ChatMessage(
                user_id=current_user.id,
                role='user',
                content=user_input,
                timestamp=datetime.utcnow(),
                session_id=session['session_id']
                )
        db.session.add(user_message)
        db.session.commit()

        detected_emotion = detect_sentiment_with_gemini(user_input)
        if analyze_intent_with_gemini(user_input):
            assistant_response = search_gospel_song(detected_emotion)
        else:
            chat_history_for_gemini = []
            if user_instruction:
                chat_history_for_gemini.append(
                        {
                            "role": "user",
                            "parts": [user_instruction.content]
                        }
                    )

            if assistant_instruction:
                chat_history_for_gemini.append(
                        {
                            "role": "assistant",
                            "parts": [assistant_instruction.content]
                        }
                    )

            for message in chat_history_query:
                chat_history_for_gemini.append(
                        {
                            "role": message.role,
                            "parts": [
                                process_message_for_bold_and_paragraphs(
                                    message.content
                                )
                            ]
                        }
                    )

            assistant_response = generative_ai_response(
                    user_input, chat_history_for_gemini
                )

        # save assistant response to the database
        assistant_message = ChatMessage(
                user_id=current_user.id,
                role='assistant',
                content=assistant_response,
                timestamp=datetime.utcnow(),
                session_id=session['session_id']
                )
        db.session.add(assistant_message)
        db.session.commit()

        return jsonify(
                {
                    "user_input": user_input,
                    "assistant_response": assistant_response
                }
            )

    chat_sessions = db.session.query(ChatMessage.session_id) \
        .filter_by(user_id=current_user.id) \
        .group_by(ChatMessage.session_id) \
        .order_by(db.func.max(ChatMessage.timestamp).desc()) \
        .all()
    chat_files = [session_id[0] for session_id in chat_sessions]

    return render_template(
            "chat.html",
            history=chat_history,
            user_instruction=user_instruction,
            assistant_instruction=assistant_instruction,
            chat_files=chat_files,
            get_chat_preview=get_chat_preview,
            )


@app.route("/new_chat", methods=["GET", "POST"])
@login_required
def new_chat():
    """
    Starts a new chat session by generating a new session ID.
    Saves the user's message if it's non-empty and redirects to the chat page.

    Returns:
        Redirects to the chat page after creating a new chat session.
    """
    session['session_id'] = generate_session_id()

    if request.method == "POST":
        user_message = request.form.get('user_feeling')

        # only save the chat if content is not empty
        if user_message.strip():
            save_chat_history(
                    current_user.id,
                    session['session_id'], [user_message]
                )
        else:
            return redirect(url_for('new_chat'))

    return redirect(url_for("chat_page"))


@app.route("/load_chats")
@login_required
def load_chats():
    """
    Loads and displays a list of chat files for the logged-in user.

    Returns:
        Response: Renders the load_chats page with the user's chat files.
    """
    user_id = current_user.id
    chat_files = get_chat_files_for_user(user_id)
    return render_template("load_chats.html", chat_files=chat_files)


@app.route("/load_chat/<session_id>")
@login_required
def load_chat(session_id):
    """
    Loads a specific chat session and updates the current session ID.

    Returns:
        Redirects to the chat page with the selected chat session loaded.
    """
    chat_history = load_chat_history(current_user.id, session_id)
    session['session_id'] = session_id
    return redirect(url_for("chat_page"))


@app.route("/delete_chat/<session_id>", methods=["GET", "POST"])
@login_required
def delete_chat(session_id):
    """
    Deletes a specific chat session and invalidates relevant caches.

    Returns:
        Redirects to the new chat page if the deleted session was active,
        otherwise redirects to the current chat page.
    """
    current_session_id = session.get('session_id')
    try:
        ChatMessage.query.filter_by(
                user_id=current_user.id, session_id=session_id
            ).delete()
        db.session.commit()

        cache.delete_memoized(get_chat_files_for_user, current_user.id)
        cache.delete_memoized(load_chat_history, current_user.id, session_id)
        cache.delete_memoized(get_chat_preview, current_user.id, session_id)
        flash('Chat deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting chat: {e}", 'error')

    if current_session_id == session_id:
        session.pop('session_id', None)
        return redirect(url_for('new_chat'))

    return redirect(url_for('chat_page'))
