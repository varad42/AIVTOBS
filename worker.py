from dotenv import load_dotenv
load_dotenv()

from modules.queue_worker import preload_whisper_model, recover_interrupted_jobs, worker_loop


if __name__ == "__main__":
    recover_interrupted_jobs()
    preload_whisper_model()
    worker_loop()
