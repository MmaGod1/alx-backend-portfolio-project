# **HeartPsalm**

HeartPsalm is a web-based application designed to uplift and encourage users by connecting their emotions with the wisdom of Bible verses and gospel music. By simply describing how they feel, users receive personalized Bible verses to inspire hope and strength. If they want more, HeartPsalm can recommend a gospel song to further uplift their spirit.

---

## **Features**
- **Emotion-Based Verse Recommendations**: Users can describe their emotions, and HeartPsalm will provide a Bible verse tailored to their feelings.
- **Music Recommendations**: When users request a song, HeartPsalm offers gospel music suggestions aligned with their emotional state.
- **Interactive Front-End**: The app uses AJAX to provide seamless communication between the user and the server, offering a dynamic and real-time experience.

---

## **Technologies Used**

### **Backend**
- **Python**: Core programming language for app functionality.
- **Flask**: Lightweight web framework to handle server-side logic and routing.
- **Flask Extensions**:
  - Flask-Login (authentication)
  - Flask-SQLAlchemy (database management)
  - Flask-Migrate (database migrations)
  - Flask-Bcrypt (password hashing)
  - Flask-Caching (integrated with Redis for efficient caching and performance optimization)


### **Frontend**
- **HTML, CSS, and JavaScript**: For creating a responsive and user-friendly interface.
- **AJAX**: To enable smooth and interactive communication without refreshing the page.

### **APIs**
- **Gemini-AI API**: Used for analyzing user input and dynamically recommending Bible verses and songs.
- **Spotify API (via Spotipy)**: For fetching gospel song recommendations.

---

## **Installation**

### **Requirements**
- Python 3.10+
- A virtual environment (optional but recommended)

### **Setup Instructions**
1. Clone the repository:
   ```bash
   git clone https://github.com/MmaGod1/alx-backend-portfolio-project/HeartPsalm
   cd HeartPsalm
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:
   ```bash
   python run.py # or python3 run.py
   ```

5. Access the app in your browser at `http://127.0.0.1:5000`.

---

## **Usage**
1. Navigate to the HeartPsalm homepage.
2. Register as a user and click `Create account`, and you're in.
3. In the chat page, type in how you’re feeling in the input box.
4. The app will provide:
   - A Bible verse to encourage you.
   - An option to request a gospel song for additional upliftment.

---

## **Code Overview**

### **Frontend**
The app’s frontend includes a simple yet effective design. It uses AJAX for smooth interactions without refreshing the page. Below is an example of how the user input is handled:

```javascript
document
  .getElementById("chat-form")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const userFeeling = document.getElementById("user_feeling").value.trim();
    if (!userFeeling) return;

    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({ user_feeling: userFeeling }),
    });

    if (response.ok) {
      const data = await response.json();
      // Dynamically update the chatbox with the assistant's response
    } else {
      console.error("Failed to send message");
    }
  });
```

---


#### **Core Backend Logic: Handling Chat Messages**

```python
@login_required
def chat_page():
    """
    Handles user chat interactions:
    - Fetches chat history and configurations.
    - Processes user input to analyze sentiment and intent.
    - Generates AI-based responses and stores messages in the database.
    """
    # Ensure session ID for the user
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()

    # Retrieve chat history from the database
    chat_history = ChatMessage.query.filter_by(
        user_id=current_user.id, session_id=session['session_id']
    ).order_by(ChatMessage.timestamp).all()

    # Load instructions for the assistant
    user_instruction = ChatConfiguration.query.filter_by(role='user').first()
    assistant_instruction = ChatConfiguration.query.filter_by(role='assistant').first()

    if request.method == "POST":
        user_input = request.form.get("user_feeling", "").strip()
        if not user_input:
            return jsonify({"error": "Message cannot be empty"}), 400

        # Save user input to the database
        user_message = ChatMessage(
            user_id=current_user.id,
            role='user',
            content=user_input,
            timestamp=datetime.utcnow(),
            session_id=session['session_id']
        )
        db.session.add(user_message)
        db.session.commit()

        # Analyze user input for emotion and intent
        detected_emotion = detect_sentiment_with_gemini(user_input)
        if analyze_intent_with_gemini(user_input):
            assistant_response = search_gospel_song(detected_emotion)
        else:
            # Generate a response using the AI model
            chat_history_for_gemini = [
                {"role": "user", "parts": [user_instruction.content]},
                {"role": "assistant", "parts": [assistant_instruction.content]}
            ] if user_instruction and assistant_instruction else []

            for msg in chat_history:
                chat_history_for_gemini.append(
                    {"role": msg.role, "parts": [msg.content]}
                )
            assistant_response = generative_ai_response(user_input, chat_history_for_gemini)

        # Save assistant's response to the database
        assistant_message = ChatMessage(
            user_id=current_user.id,
            role='assistant',
            content=assistant_response,
            timestamp=datetime.utcnow(),
            session_id=session['session_id']
        )
        db.session.add(assistant_message)
        db.session.commit()

        return jsonify({"user_input": user_input, "assistant_response": assistant_response})

    return render_template("chat.html", history=chat_history)
```

---

- **Purpose:** This function handles the chat logic, enabling users to interact with the assistant and receive Bible verse or song recommendations based on their emotions.
- **Key Steps:**
  1. Fetch the chat history and instructions from the database.
  2. Save the user input to maintain chat continuity.
  3. Analyze user emotions and intent using AI.
  4. Generate dynamic responses based on detected emotions or user input.
  5. Save the assistant’s response to the database for future reference.

---

### How It Works:
- When a user submits their message via the chat interface, this function:
  - Processes the input.
  - Analyzes sentiment and intent using the **Gemini AI API**.
  - Dynamically recommends a Bible verse or song or generates a custom AI response.
  - Updates the chat history visible to the user.

---

## **Dependencies**
The project uses the following frameworks and libraries:

```plaintext
alembic==1.14.0
annotated-types==0.7.0
bcrypt==4.2.1
blinker==1.9.0
cachelib==0.9.0
cachetools==5.5.0
certifi==2024.12.14
charset-normalizer==3.4.1
click==8.1.8
dnspython==2.7.0
email_validator==2.2.0
Flask==3.1.0
Flask-Bcrypt==1.0.1
Flask-Caching==2.3.0
Flask-Login==0.6.3
Flask-Migrate==4.0.7
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.2
google-ai-generativelanguage==0.6.10
google-api-core==2.24.0
google-api-python-client==2.156.0
google-auth==2.37.0
google-auth-httplib2==0.2.0
google-generativeai==0.8.3
greenlet==3.1.1
grpcio==1.67.1
httplib2==0.22.0
idna==3.10
itsdangerous==2.2.0
Jinja2==3.1.5
Mako==1.3.8
MarkupSafe==3.0.2
proto-plus==1.25.0
protobuf==5.29.2
pyasn1==0.6.1
pyasn1_modules==0.4.1
pycodestyle==2.12.1
pydantic==2.10.4
pydantic_core==2.27.2
pyparsing==3.2.0
redis==5.2.1
requests==2.32.3
rsa==4.9
spotipy==2.24.0
SQLAlchemy==2.0.36
tqdm==4.67.1
typing_extensions==4.12.2
uritemplate==4.1.1
urllib3==2.3.0
Werkzeug==3.1.3
WTForms==3.2.1
```

---

## **Future Features**
- Enhanced AI capabilities for deeper emotional analysis.
- Improved user interface for a more engaging experience.
- Expanded song library with genre-based filtering.
- Addition of speech to text.

---

## **Acknowledgments**
- The ALX Software Engineering Program for providing guidance and resources.
- Open-source developers whose tools and libraries powered this project.
