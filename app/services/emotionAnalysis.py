from transformers import pipeline

classifier = pipeline("text-classification", model= "j-hartmann/emotion-english-distilroberta-base", top_k=None)

def analyzeEmotion(text):
    scores = classifier(text)[0]
    emotionScores = {score['label']:round(score['score'], 2) for score in scores}
    dominantEmotion = max(emotionScores, key=emotionScores.get)
    return {
        "dominant_emotion": dominantEmotion,
        "emotion_scores": emotionScores
    }
    
                    