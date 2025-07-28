from flask import Blueprint, jsonify, request
from app.services.emotionAnalysis import analyzeEmotion
from app.config.db import supabase
import uuid
from datetime import datetime

text = Blueprint('text', __name__)

@text.route('/', methods=['POST'])
def submit():
    data = request.get_json()
    text_entry = data.get('text')
    user_id = data.get('user_id', 'anonymous')
    if not text_entry:
        return jsonify({"error": "No text provided"}), 400
    
    results = analyzeEmotion(text_entry)
    
    return jsonify({"message": "Entry saved", "results": results}), 201
 
        
    