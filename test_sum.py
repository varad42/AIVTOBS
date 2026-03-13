from transformers import pipeline

pipe = pipeline("summarization", model="t5-small")

text = "Artificial intelligence is a branch of computer science that deals with building smart machines."

print(pipe(text))