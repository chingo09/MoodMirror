from flask import Flask

def create_app():
    app = Flask(__name__)
    
    from app.api.text import text
    app.register_blueprint(text, url_prefix='/api/text')
    return app 