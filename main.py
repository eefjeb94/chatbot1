from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

app = FastAPI()

origins = [
    "http://localhost:5174",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

from openai import OpenAI

client = OpenAI()
import os
import json
import requests

elevenlabs_key = os.getenv("ELEVENLABS_KEY")

@app.get("/")
async def root():
    return {"message": "Hello World2"}

@app.post("/talk")
async def post_audio(file: UploadFile):
    user_message = transcribe_audio(file)
    print(user_message)
    chat_response = get_chat_response(user_message)
    audio_output = text_to_speech(chat_response)
    def iterfile():
        yield audio_output

    return StreamingResponse(iterfile(), media_type="application/octet-stream")

@app.get("/clear")
async def clear_history():
    file = 'database.json'
    open(file, 'w')
    return {"message": "Gegevens zijn gewist"}

def iterfile(audio_output): 
    yield audio_output

@app.get("/type")
async def get_text(text: str):
    chat_response = get_chat_response({"role": "user", "content": text})
    return chat_response.choices[0].message.content
   
@app.get("/clear")
async def clear_history():
    file = 'database.json'
    try:
        open(file, 'w').close()
        return {"message": "Chat history has been cleared"}
    except Exception as e:
        return {"error": str(e)}

# Functions
def transcribe_audio(file):
    # Save the blob first
    with open(file.filename, 'wb') as buffer:
        buffer.write(file.file.read())
    audio_file = open(file.filename, "rb")
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    transcript = {"role": "user", "content": transcript.text}
    return transcript

def get_chat_response(user_message):
    content = (user_message['content'])
    messages = load_messages()
    messages.append({"role": "user", "content": content})  
    # Send to ChatGpt/OpenAi
    gpt_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    save_messages(user_message, gpt_response)
    return gpt_response.choices[0].message.content

def load_messages():
    messages = []
    file = 'database.json'

    empty = os.stat(file).st_size == 0

    if not empty: 
            with open(file) as db_file:
                 data = json.load(db_file)
                 for item in data:
                      messages.append(item)

    else:
            messages.append(
                 {"role": "system", "content": "Je bent een recruiter en interviewt de gebruiker voor een job als marketeer. Stel gerichte vragen die relevant zijn voor een junior marketeer. Jouw naam is Jobat. Mijn naam is Eva. Zorg dat de antwoorden onder de 20 woorden zijn. Houd het professioneel met een kwinkslag."}
            )
    return messages  


def save_messages(user_message, gpt_response):
    file = 'database.json'
    messages = load_messages()

    # Ensure only the 'content' from the user_message is saved, not the entire object
    user_content = user_message['content'] if 'content' in user_message else "Invalid user message format"
    
    # Extract the GPT response content. This assumes the response structure is correctly received from GPT.
    assistant_content = gpt_response.choices[0].message.content if gpt_response.choices else "No GPT response"

    # Append both user and assistant messages
    messages.append({"role": "user", "content": user_content})
    messages.append({"role": "assistant", "content": assistant_content})

    # Save the updated messages list back to the file
    with open(file, 'w') as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)


def text_to_speech(text):
    voice_id = 'SODMYnlAYYkBrI5MpmIP'
    body = {
         "text": text,
         "model_id": "eleven_multilingual_v2",
         "voice_settings": {
            "similarity_boost": 0,
            "stability": 0,
            "style": 0.5,
            "use_speaker_boost": True
        }

    }


    headers = {
    "Content-Type": "application/json",
    "accept": "audio/mpeg",
    "xi-api-key": elevenlabs_key 
    }



    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    try:
        response = requests.post(url, json=body, headers=headers)
        print(response.status_code)
        if response.status_code == 200:
            return response.content
        else:
           error_message = f'Fout bij het converteren van tekst naar spraak: {response.status_code}'
           print(error_message)
           return error_message.encode()
    except Exception as e:
        error_message = f'Uitzondering bij het converteren van tekst naar spraak: {e}'
        print(error_message)
    return error_message.encode()

#1. Send in audio, and have it transcribed
#2. We want to send it to chatgpt and get a response
#3. We want to save the chat history to send back and forth for context


