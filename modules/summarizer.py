from transformers import pipeline
from collections import Counter
import gc
import os
import re
import requests
import math

from config import LLAMA_CPP_MODEL, LLAMA_CPP_URL

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
TRANSCRIPT_FILLER_WORDS = {
    "uh", "uhh", "um", "umm", "erm", "ah", "hmm"
}


def _resolve_model_id(model_name):
    if model_name == "hybrid":
        return None

    if model_name == "llama_cpp":
        return None

    if model_name == "t5":
        return "t5-small"

    if model_name == "distilbart":
        return "sshleifer/distilbart-cnn-12-6"

    if model_name == "long_t5":
        return "google/long-t5-tglobal-base"

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


def clean_transcript_text(text):

    if not text:
        return ""

    cleaned_text = text.replace("\r", " ")

    # Remove timestamp-like artifacts that can slip into transcripts.
    cleaned_text = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", " ", cleaned_text)
    cleaned_text = re.sub(r"\[(?:music|applause|laughter|noise)[^\]]*\]", " ", cleaned_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(r"\((?:music|applause|laughter|noise)[^)]*\)", " ", cleaned_text, flags=re.IGNORECASE)

    # Collapse stretched punctuation and repeated word stutters.
    cleaned_text = re.sub(r"([.,!?])\1+", r"\1", cleaned_text)
    cleaned_text = re.sub(r"\b(\w+)(?:\s+\1\b){1,}", r"\1", cleaned_text, flags=re.IGNORECASE)

    words = cleaned_text.split()
    cleaned_words = []
    previous_word = ""

    for word in words:
        stripped_word = re.sub(r"^[^\w]+|[^\w]+$", "", word).lower()

        if stripped_word in TRANSCRIPT_FILLER_WORDS:
            continue

        if stripped_word and stripped_word == previous_word:
            continue

        cleaned_words.append(word)
        previous_word = stripped_word

    cleaned_text = " ".join(cleaned_words)
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    return cleaned_text or text.strip()


def _normalize_words(text):

    return [
        word for word in re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        if word not in FAST_STOPWORDS
    ]


def format_seconds_as_timestamp(total_seconds):

    safe_seconds = max(0, int(total_seconds or 0))
    hours, remainder = divmod(safe_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return f"{minutes:02d}:{seconds:02d}"


def build_timestamped_summary(summary_text, segments):

    if not summary_text:
        return ""

    if not segments:
        return summary_text.strip()

    summary_sentences = _split_sentences(summary_text)
    if not summary_sentences:
        return summary_text.strip()

    usable_segments = []

    for segment in segments:
        text = str(segment.get("text", "")).strip()
        if not text:
            continue

        usable_segments.append(
            {
                "start": float(segment.get("start", 0.0) or 0.0),
                "text": text,
                "words": set(_normalize_words(text))
            }
        )

    if not usable_segments:
        return summary_text.strip()

    timestamped_lines = []
    segment_cursor = 0

    for sentence in summary_sentences:
        sentence_words = set(_normalize_words(sentence))
        best_index = segment_cursor
        best_score = -math.inf

        for index in range(segment_cursor, len(usable_segments)):
            segment = usable_segments[index]
            overlap = len(sentence_words & segment["words"])
            coverage = overlap / max(len(sentence_words), 1)
            distance_penalty = (index - segment_cursor) * 0.003
            score = coverage - distance_penalty

            if overlap == 0:
                score -= 0.05

            if score > best_score:
                best_score = score
                best_index = index

        matched_segment = usable_segments[best_index]
        timestamp = format_seconds_as_timestamp(matched_segment["start"])
        timestamped_lines.append(f"[{timestamp}] {sentence}")
        segment_cursor = min(best_index, len(usable_segments) - 1)

    return "\n".join(timestamped_lines)


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


def _summarize_chunk_with_pipeline(pipe, chunk):

    result = pipe(
        chunk,
        do_sample=False
    )
    return result[0]["summary_text"].strip()


def hierarchical_summarize_with_pipeline(
    text,
    model_name,
    chunk_size=1800,
    overlap_words=40,
    merge_group_size=4,
    max_passes=3
):

    pipe = get_pipeline(model_name)
    current_chunks = split_text(
        text,
        chunk_size=chunk_size,
        overlap_words=overlap_words
    )

    if not current_chunks:
        return ""

    pass_number = 0

    while len(current_chunks) > 1 and pass_number < max_passes:
        summarized_chunks = []

        for chunk in current_chunks:
            summarized_chunk = _summarize_chunk_with_pipeline(
                pipe,
                chunk
            )
            if summarized_chunk:
                summarized_chunks.append(summarized_chunk)

        if not summarized_chunks:
            return ""

        if len(summarized_chunks) == 1:
            return summarized_chunks[0]

        merged_chunks = []

        for start_index in range(0, len(summarized_chunks), merge_group_size):
            merged_chunk = "\n\n".join(
                summarized_chunks[start_index:start_index + merge_group_size]
            ).strip()
            if merged_chunk:
                merged_chunks.append(merged_chunk)

        if len(merged_chunks) >= len(current_chunks):
            current_chunks = summarized_chunks
            break

        current_chunks = merged_chunks
        pass_number += 1

    final_input = "\n\n".join(current_chunks).strip()
    if not final_input:
        return ""

    if len(current_chunks) == 1:
        return _summarize_chunk_with_pipeline(
            pipe,
            final_input
        )

    return final_input


def summarize_with_pipeline(text, model_name):

    return hierarchical_summarize_with_pipeline(
        text,
        model_name
    )


def build_summary_prompt(text):

    return (
        "Write a concise, high-quality summary of the following transcript. "
        "Focus on the main ideas, important details, and keep it readable.\n\n"
        f"Transcript:\n{text}"
    )


def is_llama_cpp_available(timeout=2):

    try:
        response = requests.get(
            f"{LLAMA_CPP_URL.rstrip('/')}/health",
            timeout=timeout
        )
        return response.ok
    except requests.RequestException:
        return False


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

    transcript_chunks = split_text(
        text,
        chunk_size=1400,
        overlap_words=60
    )
    condensed_parts = []

    for chunk in transcript_chunks:
        condensed_chunk = fast_extractive_summary(
            chunk,
            max_sentences=selected_sentence_count,
            chunk_sentence_limit=16
        )
        if condensed_chunk:
            condensed_parts.append(condensed_chunk)

    condensed_text = " ".join(condensed_parts).strip()

    if not condensed_text.strip():
        return ""

    try:
        return hierarchical_summarize_with_pipeline(
            condensed_text,
            "distilbart",
            chunk_size=1000,
            overlap_words=30,
            merge_group_size=3,
            max_passes=3
        )
    except Exception:
        return condensed_text


def summarize_text(text, model_name):
    cleaned_text = clean_transcript_text(text)

    if model_name == "hybrid":
        return hybrid_summary(cleaned_text)

    if model_name == "llama_cpp":
        return summarize_with_llama_cpp(cleaned_text)

    return summarize_with_pipeline(cleaned_text, model_name)
