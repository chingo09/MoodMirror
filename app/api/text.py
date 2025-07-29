from flask import Blueprint, jsonify, request
from app.services.emotionAnalysis import analyzeEmotion
from app.config.db import supabase
import uuid
from datetime import datetime

text = Blueprint('text', __name__)

# Submit text entries
@text.route('/', methods=['POST'])
def submit_text_entries():
    data = request.get_json()
    text_entry = data.get('text')
    user_id = data.get('user_id', 'anonymous')
    source = data.get('source', 'text')
    if not text_entry:
        return jsonify({"error": "No text provided"}), 400
    
    results = analyzeEmotion(text_entry)
    
    entry_id = str(uuid.uuid4())
 
    try:
         # Create a journal
        supabase.table('text_entries').insert({
            "id": entry_id,
            "user_id": user_id,
        }).execute()
        # Create first update
        supabase.table('text_updates').insert({
            "id": str(uuid.uuid4()),
            "entry_id": entry_id,
            "source": source,
            "text": text_entry,
            "dominant_emotion": results["dominant_emotion"],
            "emotion_scores": results["emotion_scores"],
            "created_at": datetime.utcnow().isoformat()
        }).execute()

    except Exception as e:
        return jsonify({"error": "Failed to save entries", "details": str(e)}), 500
    
    return jsonify({"message": "Journal entry created", "entry_id": entry_id, "results": results}), 201

# Get all journal entries for a user
@text.route('/<string:user_id>/full', methods=['GET'])
def get_all_full_journals(user_id):
    try:
        # Get all journal entries by the user
        entries_response = supabase.table('text_entries')\
            .select('*')\
            .eq('user_id', user_id)\
            .order("created_at", desc=True)\
            .execute()
        
        if not entries_response.data:
            return jsonify({"error": "No journal entries found"}), 404

        # For each entry, get its updates
        full_journals = []
        for entry in entries_response.data:
            entry_id = entry["id"]
            updates_response = supabase.table('text_updates')\
                .select('*')\
                .eq('entry_id', entry_id)\
                .order("created_at")\
                .execute()

            full_journals.append({
                "entry": entry,
                "updates": updates_response.data or []
            })

        return jsonify({"journals": full_journals}), 200

    except Exception as e:
        return jsonify({"error": "Failed to retrieve journals", "details": str(e)}), 500

# Get entry history
@text.route('/<string:entry_id>/history', methods=['GET'])
def get_entry_history(entry_id):
    try:
        response = supabase.table('text_updates')\
            .select('*')\
            .eq('entry_id', entry_id)\
            .order('created_at', desc=True)\
            .execute()

        if response.data is None:
            return jsonify({"error": "No updates found"}), 404
    except Exception as e:
        return jsonify({"error": "Failed to retrieve updates", "details": str(e)}), 500

    return jsonify({"entry history": response.data}), 200

# Get full journal entry with updates
@text.route('/<string:entry_id>/full', methods=['GET'])
def get_full_journal(entry_id):
    try:
        # Fetch the journal entry
        journal = supabase.table('text_entries').select('*').eq('id', entry_id).execute()
        if not journal.data:
            return jsonify({"error": "Journal entry not found"}), 404
        # Fetch all updates for this journal entry
        updates = supabase.table('text_updates').select('*').eq('entry_id', entry_id).order("created_at").execute()
        if updates.data is None or len(updates.data) == 0:
            return jsonify({
                "entry": journal.data,
                "updates": [],
                "message": "No updates found for this journal entry"
            }), 200
            
        return jsonify({
            "entry": journal.data,
            "updates": updates.data
        }), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve journal", "details": str(e)}), 500
 
 # Update a text entry       
@text.route('/<string:entry_id>', methods=['PUT'])
def update_text_entry(entry_id):
    data = request.get_json()
    new_text = data.get('text')
    source = data.get('source', 'text')
    
    if not new_text:
        return jsonify({"error":"No text provided"}), 400
    
    results = analyzeEmotion(new_text)
    
    try:
        # Update the text entry
        supabase.table('text_updates').insert({
            "id": str(uuid.uuid4()),
            "entry_id": entry_id,
            "source": source,
            "text": new_text,
            "dominant_emotion": results["dominant_emotion"],
            "emotion_scores": results["emotion_scores"],
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        return jsonify({"error":"Failed to update entry", "details": str(e)}), 500
    
    return jsonify({"message":"Entry updated", "results": results}), 200
