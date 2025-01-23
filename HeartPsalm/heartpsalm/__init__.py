from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import google.generativeai as genai
from flask_caching import Cache
from flask_migrate import Migrate

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.app_context().push()

# Access your keys securely from the environment
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Database setup
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login_page"
login_manager.login_message_category = "info"

# Cache config
cache_config = {
    "CACHE_TYPE": os.getenv("CACHE_TYPE"),
    "CACHE_REDIS_HOST": os.getenv("CACHE_REDIS_HOST"),
    "CACHE_REDIS_PORT": os.getenv("CACHE_REDIS_PORT"),
    "CACHE_DEFAULT_TIMEOUT": os.getenv("CACHE_DEFAULT_TIMEOUT")
}

cache = Cache(app, config=cache_config)

# Spotify API Setup
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
client_credentials_manager = SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Generative AI Setup
genai.configure(api_key=os.getenv("GENERATIVE_AI_API_KEY"))

from heartpsalm import routes
