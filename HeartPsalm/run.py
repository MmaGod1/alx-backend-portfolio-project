from heartpsalm import app, db
from heartpsalm.models import create_default_config

@app.template_filter('datetime')
def format_datetime(value):
    if value is None:
        return ""
    return value.strftime('%Y-%m-%d %H:%M')

with app.app_context():
    db.create_all()
    create_default_config()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
