from transformers import pipeline


def get_pipeline(model_name):

    if model_name == "t5_small":
        return pipeline(
            "summarization",
            model="t5-small"
        )

    if model_name == "t5":
        return pipeline(
            "summarization",
            model="t5-small"
        )

    if model_name == "distilbart":
        return pipeline(
            "summarization",
            model="sshleifer/distilbart-cnn-12-6"
        )

    if model_name == "bart":
        return pipeline(
            "summarization",
            model="facebook/bart-large-cnn"
        )

    if model_name == "pegasus":
        return pipeline(
            "summarization",
            model="google/pegasus-xsum"
        )

    return pipeline(
        "summarization",
        model="t5-small"
    )


def split_text(text, chunk_size=1800):

    words = text.split()

    if not words:
        return []

    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        word_length = len(word) + 1

        if current_chunk and current_length + word_length > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = word_length
            continue

        current_chunk.append(word)
        current_length += word_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def summarize_text(text, model_name):

    pipe = get_pipeline(model_name)
    chunks = split_text(text)

    if not chunks:
        return ""

    partial_summaries = []

    for chunk in chunks:
        result = pipe(
            chunk,
            do_sample=False
        )
        partial_summaries.append(result[0]["summary_text"])

    if len(partial_summaries) == 1:
        return partial_summaries[0]

    combined_text = " ".join(partial_summaries)
    final_result = pipe(
        combined_text,
        do_sample=False
    )

    return final_result[0]["summary_text"]
