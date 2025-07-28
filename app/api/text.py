from flask import Blueprint, jsonify, request
from app.services.emotionAnalysis import analyzeEmotion
from app.config.db import supabase
import uuid
from datetime import datetime

text = Blueprint('text', __name__)

@text.route('/', methods=['POST'])
def submit_text_entries():
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
            return jsonify({"error": "Failed to save entries"}), 500
    except Exception as e:
        return jsonify({"error": "Failed to save entries", "details": str(e)}), 500
    
    return jsonify({"message": "Entry saved", "results": results}), 201

@text.route('/<string:user_id>', methods=['GET'])
def get_text_entries(user_id):
    try:
        response = supabase.table('text_entries').select('*').eq('user_id', user_id).order("created_at", desc=True).execute()
        if response.data is None:
            return jsonify({"error": "Failed to retrieve entries"}), 500
    except Exception as e:
        return jsonify({"error": "Failed to retrieve entries", "details": str(e)})
        
    return jsonify({"data": response.data}), 200
        
@text.route('/<string:entry_id>', methods=['PUT'])
def update_text_entry(entry_id):
    data = request.get_json()
    new_text = data.get('text')
    
    if not new_text:
        return jsonify({"error":"No text provided"}), 400
    
    results = analyzeEmotion(new_text)
    
    update_data = {
        "original_text": new_text,
        "dominant_emotion": results["dominant_emotion"],
        "emotion_scores": results["emotion_scores"],
        "updated_at": datetime.utcnow().isoformat()
    }
    
    try:
        response = supabase.table('text_entries').update(update_data).eq('id', entry_id).execute()
        
        if response.data is None:
            return jsonify ({"error":"Failed to update entry"}), 500
    except Exception as e:
        return jsonify({"error":"Failed to update entry", "details": str(e)}), 500
    
    return jsonify({"message":"Entry updated", "results": results}), 200
