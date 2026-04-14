from flask import Flask
from dotenv import load_dotenv
from app.routes.main_routes import main_bp
from app.ai_models.reminders.reminder_routes import reminder_bp
from app.routes.audio_routes import audio_bp

load_dotenv()

app = Flask(__name__)
app.register_blueprint(main_bp)
app.register_blueprint(reminder_bp, url_prefix='/api')
app.register_blueprint(audio_bp, url_prefix='/api')

@app.route('/')
def home():
    return 'Hello, DBMS Project!'

if __name__ == '__main__':
    app.run(debug=True)