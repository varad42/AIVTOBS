from transformers import pipeline


def get_pipeline(model_name):
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

    return pipeline(
        "summarization",
        model="t5-small"
    )


def split_text(text, chunk_size=1800, overlap_words=40):

    words = text.split()

    if not words:
        return []

    chunks = []
    start_index = 0

    while start_index < len(words):
        current_chunk = []
        current_length = 0
        index = start_index

        while index < len(words):
            word = words[index]
            word_length = len(word) + 1

            if current_chunk and current_length + word_length > chunk_size:
                break

            current_chunk.append(word)
            current_length += word_length
            index += 1

        if not current_chunk:
            current_chunk.append(words[index])
            index += 1

        chunks.append(" ".join(current_chunk))

        if index >= len(words):
            break

        start_index = max(index - overlap_words, start_index + 1)

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

    return "\n\n".join(partial_summaries)
