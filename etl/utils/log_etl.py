from datetime import datetime
import os

def log_format(header, message):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"[{now}] [{header}] {message}"

def log_write(header, message):
    m = log_format(header, message)

    print(m, flush=True)
    os.makedirs("logs", exist_ok=True)

    # escribir en archivo en modo append
    log_file_path = f"logs/etl_{header}.log"
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(m + "\n")
