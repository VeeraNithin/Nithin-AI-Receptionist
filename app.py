import os
import requests
from flask import Flask, request
from groq import Groq

app = Flask(__name__)

# Render Environment Variables (We will set these securely later)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)

@app.route('/')
def home():
    return "Nithin's AI Receptionist is Awake!"

@app.route('/voicemail', methods=['POST'])
def handle_voicemail():
    file = request.files.get('document')
    if not file:
        return "No file received", 400
        
    file_path = "caller_msgs.mp3"
    file.save(file_path)
    
    try:
        with open(file_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=(file_path, audio_file.read()),
                model="whisper-large-v3",
                response_format="text",
            )
            
        system_prompt = "Summarize this voicemail. Identify Caller Name, Purpose, and Urgency. If the caller spoke in Telugu, reply in Telugu/Tanglish script. Keep it very brief."
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcription}
            ],
            model="llama3-8b-8192",
        )
        summary = completion.choices[0].message.content
        
        final_msg = f"🚨 *NEW CALLER VOICEMAIL*\n\n*What they said:* {transcription}\n\n*AI Summary:* {summary}"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": final_msg, "parse_mode": "Markdown"})
        
        return "Success", 200
        
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": f"⚠️ Server Error: {str(e)}"})
        return "Error", 500

if __name__ == '__main__':
    # Render requires port 10000
    app.run(host='0.0.0.0', port=10000)
