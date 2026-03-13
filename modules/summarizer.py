from transformers import pipeline


def get_pipeline(model_name):

    if model_name == "t5":
        return pipeline("summarization", model="t5-small")

    if model_name == "bart":
        return pipeline("summarization", model="facebook/bart-large-cnn")

    if model_name == "pegasus":
        return pipeline("summarization", model="google/pegasus-cnn_dailymail")

    return pipeline("summarization", model="t5-small")


def summarize_text(text, model_name):

    pipe = get_pipeline(model_name)

    chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]

    summary = ""

    for c in chunks:

        s = pipe(c, max_length=150, min_length=40, do_sample=False)

        summary += s[0]["summary_text"] + "\n"

    return summary