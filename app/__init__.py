from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    CORS(app) 
    
    from app.api.text import text
    app.register_blueprint(text, url_prefix='/api/text')
    from app.api.audio import audio
    app.register_blueprint(audio, url_prefix='/api/audio')
    
        # ✅ Print all registered routes
    print("\nRegistered routes:")
    for rule in app.url_map.iter_rules():
        print(rule)
        
    return app 