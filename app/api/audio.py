from flask import Blueprint, jsonify, request
from app.services.audioTranscription import transcribe_audio
from app.services.emotionAnalysis import analyzeEmotion
from app.services.uploadService import upload_to_s3
from app.config.db import supabase
import uuid
from datetime import datetime
import tempfile
import os

audio = Blueprint('audio', __name__)

UPLOAD_FOLDER = 'app/services/uploads'

@audio.route('/', methods=['POST'])
def submit_audio_entries():
        
    try:
        if 'audio_file' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio_file']
        user_id = request.form.get('user_id', 'anonymous')
        source = request.form.get('source', 'audio')
        
        if audio_file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Upload the audio file to s3:
        s3_key = f"audio/{(uuid.uuid4())}_{audio_file.filename}"
        temp_dir = tempfile.gettempdir()
        audio_file_path = os.path.join(temp_dir, audio_file.filename)
        audio_file.save(audio_file_path)
        if not os.path.exists(audio_file_path):
            return jsonify({"error":"Failed to save audio file"}),500
        
        s3_url = upload_to_s3(audio_file_path, s3_key)
        if not s3_url:
            return jsonify({"error":"Failed to upload audio file"}), 500
        
        # Transcribe the audio file
        transcript = transcribe_audio(audio_file_path)
        if not transcript:
            return jsonify({"error": "Failed to transcribe audio"}), 500
        
        # Analyze emotions from the transcript
        results = analyzeEmotion(transcript)
        if not results:
            return jsonify({"error":"Failed to analyze emotions"}), 500
        
        # Insert into the database
        entry_id = str(uuid.uuid4())
        supabase.table("text_entries").insert({
            "id":entry_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        supabase.table("text_updates").insert({
            "id": str(uuid.uuid4()),
            "entry_id": entry_id,
            "source": source,
            "transcript": transcript,
            "dominant_emotion": results["dominant_emotion"],
            "emotion_scores": results["emotion_scores"],
            "created_at": datetime.utcnow().isoformat(),
            "audio_url": s3_url
        }).execute()
        return jsonify({
            "message":"Audio entry created",
            "entry_id": entry_id,
            "results": results,
            "audio_url": s3_url,
            "transcript": transcript
        })  
    except Exception as e:
        return jsonify({"error":"Failed to save audio entry", "details": str(e)}), 500

@audio.route('/<string:entry_id>/full', methods=['GET'])
def get_full_audio_entry(entry_id):
    try:
        # Get the entry by ID
        journal = supabase.table('text_entries').select('*').eq('id', entry_id).execute()
        if not journal.data:
            return jsonify({"error": "Journal entry not found"}), 404
        
        # Get all updates for the entry
        updates = supabase.table('text_updates').select('*').eq('entry_id', entry_id).eq('source', 'audio').order("created_at", desc=True).execute()
        return jsonify({
            "journal": journal.data[0],
            "updates": updates.data or [],
            "message": "Success" if updates.data else "No audio updates found"
        }), 200
         
    except Exception as e: 
        return jsonify({"error":"Failed to retrieve audio entry", "details": str(e)}), 500

@audio.route('/<string:entry_id>', methods=['PUT'])
def update_audio_entry(entry_id):
    try:
        if 'audio_file' not in request.files:
            return jsonify({"error":"No audio file provided"}), 400
        
        audio_file = request.files['audio_file']
        source = request.form.get('source', 'audio')
        if audio_file.filename == '':
            return jsonify({"error":"No selected file"}), 400
        
        # Upload the audio file to s3
        s3_key = f"audio/{(uuid.uuid4())}_{audio_file.filename}"
        temp_dir = tempfile.gettempdir()
        audio_file_path = os.path.join(temp_dir, audio_file.filename)
        audio_file.save(audio_file_path)
        if not os.path.exists(audio_file_path):
            return jsonify({"error":"Failed to save audio file"}), 500
        
        s3_url = upload_to_s3(audio_file_path, s3_key)
        if not s3_url:
            return jsonify({"error":"Failed to upload audio file"}), 500
        
        # Transcribe the audio file
        new_transcript = transcribe_audio(audio_file_path)
        if not new_transcript:
            return jsonify({"error":"Failed to transcribe audio"}), 500
        
        results = analyzeEmotion(new_transcript)
        if not results:
            return jsonify({"error":"Failed to analyze emotions"}), 500
        
        # Update the database
        supabase.table("text_updates").insert({
            "id": str(uuid.uuid4()),
            "entry_id": entry_id,
            "source": source,
            "transcript": new_transcript,
            "dominant_emotion": results["dominant_emotion"],
            "emotion_scores": results["emotion_scores"],
            "created_at": datetime.utcnow().isoformat(),
            "audio_url": s3_url
        }).execute()
        
        return jsonify({
            "message": "Audio entry updated",
            "entry_id": entry_id,
            "results": results,
            "audio_url": s3_url,
            "transcript": new_transcript
        })
        
    except Exception as e:
        return jsonify({"error":"Failed to update audio entry", "details": str(e)}), 500
        
@audio.route('/<string:entry_id>', methods=['DELETE'])
def delete_audio_entry(entry_id):
    try:
        # Delete all updates linked to this entry
        supabase.table('text_updates').delete().eq('entry_id', entry_id).eq('source', 'audio').execute()
        
        # Check if there are any remaining text updates
        remaining_updates = supabase.table('text_updates').select('*').eq('entry_id', entry_id).execute()

        if not remaining_updates.data:
            # If no updates left, delete the journal entry,
            supabase.table('text_entries').delete().eq('id', entry_id).execute()
            return jsonify({"message": "Audio entry and all updates deleted"}), 200
        else:
            return jsonify({"message": "Audio updates deleted, but entry still has text updates"}),200
    except Exception as e:
        return jsonify({"error": "Failed to delete audio updates", "details": str(e)}), 500