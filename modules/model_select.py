from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect
from database.mongo import jobs_collection
from modules.summarizer import is_llama_cpp_available

model_bp = Blueprint("model", __name__)
SUMMARY_MODEL_OPTIONS = [
    {
        "value": "hybrid",
        "label": "Hybrid",
        "description": "Best balance of speed and quality. Extracts key ideas first, then rewrites them with a lightweight model.",
        "checked": True,
    },
    {
        "value": "t5",
        "label": "T5",
        "description": "Solid general-purpose summarization baseline.",
    },
    {
        "value": "distilbart",
        "label": "DistilBART",
        "description": "A lighter BART variant that can be a good speed compromise.",
    },
    {
        "value": "llama_cpp",
        "label": "llama.cpp",
        "description": "Uses a local llama.cpp OpenAI-compatible server for summarization.",
    },
]
ALLOWED_SUMMARY_MODELS = {option["value"] for option in SUMMARY_MODEL_OPTIONS}


def get_available_summary_model_options():

    llama_cpp_available = is_llama_cpp_available()
    available_options = []

    for option in SUMMARY_MODEL_OPTIONS:
        option_data = dict(option)
        value = option_data["value"]

        if value == "llama_cpp":
            option_data["enabled"] = llama_cpp_available
            if not llama_cpp_available:
                option_data["description"] += " Unavailable until the local llama.cpp server is running."
        else:
            option_data["enabled"] = True

        if not option_data["enabled"]:
            option_data.pop("checked", None)

        available_options.append(option_data)

    if not any(option.get("checked") for option in available_options):
        for option in available_options:
            if option["enabled"]:
                option["checked"] = True
                break

    return available_options


@model_bp.route("/select_model/<job_id>", methods=["GET", "POST"])
def select_model(job_id):
    summary_model_options = get_available_summary_model_options()
    enabled_models = {
        option["value"]
        for option in summary_model_options
        if option["enabled"]
    }

    job = jobs_collection.find_one({"job_id": job_id})

    if not job:
        print(f"Model selection failed: job {job_id} not found")
        return "Job not found"

    if request.method == "POST":

        model = request.form.get("model")

        if model not in ALLOWED_SUMMARY_MODELS:
            print(f"Invalid model selected for job {job_id}: {model}")
            return "Invalid model selected", 400

        if model not in enabled_models:
            print(f"Unavailable model selected for job {job_id}: {model}")
            return "Selected model is currently unavailable", 400

        print(f"Model selected for job {job_id}: {model}")

        jobs_collection.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "summary_model": model,
                    "status": "summarize_requested",
                    "model_selected_at": datetime.now(timezone.utc)
                }
            }
        )

        return redirect(f"/processing/{job_id}")

    return render_template(
        "select_model.html",
        job=job,
        summary_model_options=summary_model_options
    )
