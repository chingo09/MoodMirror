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
    
    insert_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "source": "text",
        "original_text": text_entry,
        "dominant_emotion": results["dominant_emotion"],
        "emotion_scores": results ["emotion_scores"],
        "created_at": datetime.utcnow().isoformat()
    }
    
    try:
        response = supabase.table('text_entries').insert(insert_data).execute()
        
        if response.data is None:
            return jsonify({"error": "Failed to save entry"}), 500
    except Exception as e:
        return jsonify({"error": "Failed to save entry", "details": str(e)}), 500
    
    return jsonify({"message": "Entry saved", "results": results}), 201
 
        
    