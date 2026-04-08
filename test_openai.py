from openai import OpenAI

client = OpenAI()
audio_file= open("/home/ubuntu/ai_receptionist/Gravação2.m4a", "rb")

transcription = client.audio.transcriptions.create(
    model="gpt-4o-mini-transcribe", 
    file=audio_file,
    language= "pt"
)

print(transcription.text)