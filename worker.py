from dotenv import load_dotenv
load_dotenv()

from modules.queue_worker import preload_whisper_model, worker_loop


if __name__ == "__main__":
    preload_whisper_model()
    worker_loop()
