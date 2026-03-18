from transformers import pipeline
from collections import Counter
import gc
import os
import re
import requests

from config import OLLAMA_SUMMARY_MODEL, OLLAMA_URL, LLAMA_CPP_MODEL, LLAMA_CPP_URL

_PIPELINE_CACHE = {}
FAST_STOPWORDS = {
    "about", "after", "again", "also", "because", "been", "before", "being",
    "between", "both", "came", "could", "does", "doing", "during", "each",
    "from", "have", "having", "here", "into", "just", "more", "most",
    "other", "over", "same", "should", "some", "such", "than", "that",
    "their", "them", "then", "there", "these", "they", "this", "those",
    "through", "under", "very", "want", "were", "what", "when", "where",
    "which", "while", "with", "would", "your", "you", "about", "into",
    "video", "videos", "summary", "summaries"
}


def _resolve_model_id(model_name):
    if model_name == "hybrid":
        return None

    if model_name in {"ollama", "llama_cpp", "mistral", "phi"}:
        return None

    if model_name == "t5":
        return "t5-small"

    if model_name == "distilbart":
        return "sshleifer/distilbart-cnn-12-6"

    return "t5-small"


def get_pipeline(model_name):
    resolved_model_name = model_name or "t5"
    model_id = _resolve_model_id(resolved_model_name)

    if model_id is None:
        return None

    if resolved_model_name not in _PIPELINE_CACHE:
        if _PIPELINE_CACHE:
            cached_model_names = ", ".join(_PIPELINE_CACHE.keys())
            print(
                "Clearing previously cached summarization pipelines "
                f"before loading {model_id}: {cached_model_names}"
            )
            _PIPELINE_CACHE.clear()
            gc.collect()

        print(f"Loading summarization pipeline into memory: {model_id}")
        _PIPELINE_CACHE[resolved_model_name] = pipeline(
            "summarization",
            model=model_id
        )

    return _PIPELINE_CACHE[resolved_model_name]


def _split_sentences(text):

    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text.strip())
        if sentence.strip()
    ]


def _normalize_words(text):

    return [
        word for word in re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        if word not in FAST_STOPWORDS
    ]


def _sentence_similarity(sentence_a, sentence_b):

    words_a = set(_normalize_words(sentence_a))
    words_b = set(_normalize_words(sentence_b))

    if not words_a or not words_b:
        return 0.0

    return len(words_a & words_b) / len(words_a | words_b)


def _score_sentence(sentence, index, total_sentences, word_scores):

    sentence_words = _normalize_words(sentence)
    if not sentence_words:
        return None

    frequency_score = sum(word_scores[word] for word in sentence_words) / len(sentence_words)
    unique_word_bonus = len(set(sentence_words)) / max(len(sentence_words), 1)

    # Favor earlier sentences a bit because transcripts often introduce key ideas early.
    early_position_bonus = max(0.0, 1 - (index / max(total_sentences, 1))) * 0.35

    sentence_length = len(sentence_words)
    if sentence_length < 6:
        length_multiplier = 0.7
    elif sentence_length > 35:
        length_multiplier = 0.85
    else:
        length_multiplier = 1.0

    return (frequency_score + unique_word_bonus + early_position_bonus) * length_multiplier


def _select_top_sentences(sentences, max_sentences):

    words = _normalize_words(" ".join(sentences))
    if not words:
        return sentences[:max_sentences]

    word_scores = Counter(words)
    scored_sentences = []

    for index, sentence in enumerate(sentences):
        score = _score_sentence(sentence, index, len(sentences), word_scores)
        if score is None:
            continue
        scored_sentences.append((score, index, sentence))

    if not scored_sentences:
        return sentences[:max_sentences]

    selected = []

    for _, index, sentence in sorted(scored_sentences, reverse=True):
        if any(_sentence_similarity(sentence, chosen_sentence) > 0.7 for _, chosen_sentence in selected):
            continue

        selected.append((index, sentence))
        if len(selected) >= max_sentences:
            break

    if not selected:
        selected = [(index, sentence) for _, index, sentence in scored_sentences[:max_sentences]]

    return [sentence for index, sentence in sorted(selected, key=lambda item: item[0])]


def fast_extractive_summary(text, max_sentences=6, chunk_sentence_limit=18):

    sentences = _split_sentences(text)

    if not sentences:
        return text.strip()

    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    if len(sentences) > chunk_sentence_limit:
        chunk_summaries = []

        for start_index in range(0, len(sentences), chunk_sentence_limit):
            sentence_chunk = sentences[start_index:start_index + chunk_sentence_limit]
            selected_chunk_sentences = _select_top_sentences(sentence_chunk, max(2, min(4, max_sentences)))
            if selected_chunk_sentences:
                chunk_summaries.append(" ".join(selected_chunk_sentences))

        condensed_sentences = _split_sentences(" ".join(chunk_summaries))
        if condensed_sentences:
            sentences = condensed_sentences

    return " ".join(_select_top_sentences(sentences, max_sentences))


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


def summarize_with_pipeline(text, model_name):

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


def build_summary_prompt(text):

    return (
        "Write a concise, high-quality summary of the following transcript. "
        "Focus on the main ideas, important details, and keep it readable.\n\n"
        f"Transcript:\n{text}"
    )


def is_ollama_available(timeout=2):

    try:
        response = requests.get(
            f"{OLLAMA_URL.rstrip('/')}/api/tags",
            timeout=timeout
        )
        return response.ok
    except requests.RequestException:
        return False


def is_llama_cpp_available(timeout=2):

    try:
        response = requests.get(
            f"{LLAMA_CPP_URL.rstrip('/')}/health",
            timeout=timeout
        )
        return response.ok
    except requests.RequestException:
        return False


def summarize_with_ollama(text, model_name=None):
    selected_model = model_name or OLLAMA_SUMMARY_MODEL
    base_url = OLLAMA_URL.rstrip("/")
    prompt = build_summary_prompt(text)

    if not is_ollama_available():
        raise RuntimeError(
            f"Ollama is not reachable at {base_url}. "
            "Start the Ollama server and make sure the selected model is installed."
        )

    endpoint_attempts = [
        (
            f"{base_url}/api/generate",
            {
                "model": selected_model,
                "prompt": prompt,
                "stream": False
            },
            "generate"
        ),
        (
            f"{base_url}/api/chat",
            {
                "model": selected_model,
                "stream": False,
                "messages": [
                    {
                        "role": "system",
                        "content": "You write concise, high-quality transcript summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "chat"
        ),
        (
            f"{base_url}/v1/chat/completions",
            {
                "model": selected_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You write concise, high-quality transcript summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.2
            },
            "openai_chat"
        )
    ]

    last_error = None

    for url, payload, response_type in endpoint_attempts:
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=300
            )

            if response.status_code == 404:
                last_error = RuntimeError(
                    f"Endpoint not found at {url}"
                )
                continue

            response.raise_for_status()
            data = response.json()

            if response_type == "generate":
                return data.get("response", "").strip()

            if response_type == "chat":
                return data.get("message", {}).get("content", "").strip()

            return data["choices"][0]["message"]["content"].strip()
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as error:
            last_error = error

    raise RuntimeError(
        "Could not reach a compatible Ollama endpoint. "
        f"Checked {base_url}/api/generate, {base_url}/api/chat, and "
        f"{base_url}/v1/chat/completions for model '{selected_model}'. "
        "Make sure Ollama is running and that the model has been pulled locally."
    ) from last_error


def summarize_with_llama_cpp(text):

    if not is_llama_cpp_available():
        raise RuntimeError(
            f"llama.cpp server is not reachable at {LLAMA_CPP_URL.rstrip('/')}. "
            "Start the llama.cpp server before selecting this model."
        )

    response = requests.post(
        f"{LLAMA_CPP_URL.rstrip('/')}/v1/chat/completions",
        json={
            "model": LLAMA_CPP_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You write concise, high-quality transcript summaries."
                },
                {
                    "role": "user",
                    "content": build_summary_prompt(text)
                }
            ],
            "temperature": 0.2
        },
        timeout=300
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def hybrid_summary(text):

    sentences = _split_sentences(text)

    if not sentences:
        return text.strip()

    if len(sentences) <= 8:
        return fast_extractive_summary(text, max_sentences=4)

    if len(sentences) <= 20:
        selected_sentence_count = 6
    elif len(sentences) <= 40:
        selected_sentence_count = 8
    else:
        selected_sentence_count = 10

    condensed_text = fast_extractive_summary(
        text,
        max_sentences=selected_sentence_count,
        chunk_sentence_limit=16
    )

    if not condensed_text.strip():
        return ""

    try:
        return summarize_with_pipeline(condensed_text, "distilbart")
    except Exception:
        return condensed_text


def summarize_text(text, model_name):
    if model_name == "hybrid":
        return hybrid_summary(text)

    if model_name == "ollama":
        return summarize_with_ollama(text)

    if model_name == "mistral":
        return summarize_with_ollama(text, "mistral")

    if model_name == "phi":
        return summarize_with_ollama(text, "phi")

    if model_name == "llama_cpp":
        return summarize_with_llama_cpp(text)

    return summarize_with_pipeline(text, model_name)
