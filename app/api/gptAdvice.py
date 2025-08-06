from flask import Blueprint, jsonify, request
from app.config.db import supabase
from app.config.openai import client
from uuid import uuid4
from datetime import datetime
import hashlib

gptAdvice = Blueprint('gptAdvice', __name__)

def compute_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

@gptAdvice.route('/advice/<string:entry_id>', methods=['GET'])
def get_gpt_advice(entry_id):
    try:
        journal = supabase.table("text_entries") \
            .select("*") \
            .eq("id", entry_id) \
            .limit(1) \
            .execute()
        
        if not journal.data:
            return jsonify({"error": "Journal entry not found"}), 404
        entry_info = journal.data[0]

        updates = supabase.table("text_updates") \
            .select("text, transcript, created_at") \
            .eq("entry_id", entry_id) \
            .order("created_at", desc=False) \
            .execute()

        if not updates.data:
            return jsonify({"error": "No updates found for this entry"}), 404

        full_journal = ""
        for update in updates.data:
            content = update.get("text") or update.get("transcript")
            if content:
                full_journal += f"- {content}\n"

        # Compute hash of the full journal content
        text_hash = compute_text_hash(full_journal)

        # Check if cached advice exists
        cached = supabase.table("gpt_advice") \
            .select("*") \
            .eq("text_hash", text_hash) \
            .limit(1) \
            .execute()

        if cached.data:
            cached_advice = cached.data[0]
            return jsonify({
                "entry_text": full_journal.strip(),
                "summary": cached_advice["summary"],
                "recommendation": cached_advice["recommendation"],
                "response_generated_at": cached_advice["created_at"],
                "entry_created_at": entry_info["created_at"],
                "advice_id": cached_advice["id"],
                "cached": True
            })

        # 🔄 No cached advice, generate summary
        summary_prompt = f"""Please summarize the following emotional journal written over time in 2–3 sentences.

Journal:
{full_journal}
"""
        summary_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful mental health assistant."},
                {"role": "user", "content": summary_prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        summary = summary_response.choices[0].message.content.strip()

        if not summary:
            return jsonify({"error": "Failed to generate summary"}), 500

        # 💡 Generate recommendation
        recommendation_prompt = f"""Based on this emotional journal, what supportive advice or mental health recommendation would you give the user? Be encouraging and thoughtful.

Journal:
{full_journal}
"""
        recommendation_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful mental health assistant."},
                {"role": "user", "content": recommendation_prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        recommendation = recommendation_response.choices[0].message.content.strip()

        if not recommendation:
            return jsonify({"error": "Failed to generate recommendation"}), 500

        # 💾 Save result with hash
        advice_id = str(uuid4())
        insert_result = supabase.table("gpt_advice").insert({
            "id": advice_id,
            "entry_id": entry_id,
            "text_hash": text_hash,
            "summary": summary,
            "recommendation": recommendation,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        if not insert_result.data:
            return jsonify({"error": "Failed to save GPT advice"}), 500

        return jsonify({
            "entry_text": full_journal.strip(),
            "summary": summary,
            "recommendation": recommendation,
            "response_generated_at": datetime.utcnow().isoformat(),
            "entry_created_at": entry_info["created_at"],
            "advice_id": advice_id,
            "cached": False
        })

    except Exception as e:
        return jsonify({"error": "Failed to generate GPT advice", "details": str(e)}), 500
