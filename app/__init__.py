from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    CORS(app) 
    
    from app.api.text import text
    app.register_blueprint(text, url_prefix='/api/text')
    return app 