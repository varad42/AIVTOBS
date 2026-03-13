import whisper

model = whisper.load_model("base")

result = model.transcribe("jobs/test.wav")

print(result["text"])