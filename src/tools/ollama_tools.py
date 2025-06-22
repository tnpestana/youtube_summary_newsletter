import subprocess
import time
import signal

from contextlib import contextmanager

@contextmanager
def managed_ollama():
    proc = start_ollama()
    try:
        if not wait_for_ollama_ready():
            raise RuntimeError("Ollama did not start in time.")
        yield
    finally:
        stop_ollama(proc)

def start_ollama():
    print("🦙 Starting Ollama...")
    return subprocess.Popen(["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def stop_ollama(process):
    print("🦙 Stopping Ollama...")
    process.send_signal(signal.SIGINT)  # Gracefully stop with Ctrl+C signal
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        print("🦙 Force killing Ollama...")
        process.kill()

def wait_for_ollama_ready(timeout=30):
    import requests
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get("http://localhost:11434")
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False