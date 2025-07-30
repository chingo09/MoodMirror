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
@text.route('/user/<string:user_id>/full', methods=['GET'])
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

@text.route('/journal/<string:entry_id>/full', methods=['GET'])
def get_full_journal(entry_id):
    try:
        entry_id = entry_id.strip()
        print("🔍 Looking for entry_id:", entry_id)

        journal = supabase.table('text_entries').select('*').eq('id', entry_id).execute()
        print("📄 Query result:", journal.data)

        if not journal.data:
            return jsonify({"error": "Journal entry not found"}), 404

        updates = supabase.table('text_updates').select('*').eq('entry_id', entry_id).order("created_at").execute()
        print("📝 Update results:", updates.data)

        return jsonify({
            "entry": journal.data[0],
            "updates": updates.data or [],
            "message": "Success" if updates.data else "No updates found"
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

# Delete a journal entry and its updates
@text.route('/<string:entry_id>/journal', methods=['DELETE'])
def delete_journal(entry_id):
    try:
        # Delete all updates linked to this entry
        supabase.table('text_updates').delete().eq('entry_id', entry_id).execute()

        # Delete the journal entry itself
        response = supabase.table('text_entries').delete().eq('id', entry_id).execute()

        if response.data is None:
            return jsonify({"error": "Entry not found or could not be deleted"}), 404
    except Exception as e:
        return jsonify({"error": "Failed to delete entry", "details": str(e)}), 500

    return jsonify({"message": "Journal and its updates deleted successfully"}), 200

# Delete a specific text update
@text.route('/<string:update_id>/one', methods=['DELETE'])
def delete_text_by_id(update_id):
    try:
        result = supabase.table('text_updates').select('*').eq('id', update_id).eq('source', 'text').execute()
        if not result.data:
            return jsonify({"message": "Text not found"}), 404
        
        # Delete the specific audio update
        response = supabase.table('text_updates').delete().eq('id', update_id).eq('source', 'text').execute()
        return jsonify({"message":"Text deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": "Failed to delete text", "details": str(e)}), 500