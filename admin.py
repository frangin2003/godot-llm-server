import subprocess
import time
import sys
import datetime
import signal
import os

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[ADMIN] [{timestamp}] {message}")
    sys.stdout.flush()

def start_server(port, model_name, additional_args=[]):
    cmd = [sys.executable, "-u", "run.py", str(port), model_name] + additional_args
    log(f"Starting server with command: {' '.join(cmd)}")
    
    # Log file setup
    log_file = open('server_log.txt', 'a')
    log_file.write(f"\n\n=== New Server Start: {datetime.datetime.now()} ===\n")
    log_file.flush()
    
    try:
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            env={**os.environ, 'PYTHONUNBUFFERED': '1'},
            universal_newlines=True,
            encoding='utf-8'
        )
    except Exception as e:
        error_msg = f"Failed to start server: {e}"
        log(error_msg)
        log_file.write(f"{error_msg}\n")
        log_file.flush()
        raise

def monitor_server():
    if len(sys.argv) < 3:
        print("Usage: python admin.py <port> <model_name> [additional args...]")
        sys.exit(1)

    port = sys.argv[1]
    model_name = sys.argv[2]
    additional_args = sys.argv[3:]
    restart_delay = 1
    max_restart_delay = 30
    restarts = 0

    def signal_handler(signum, frame):
        log(f"Received signal {signum}. Shutting down admin...")
        if process and process.poll() is None:
            log("Terminating server process...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                log("Server didn't terminate gracefully, forcing...")
                process.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while True:
        try:
            process = start_server(port, model_name, additional_args)
            restarts += 1
            log(f"Server started (restart #{restarts})")

            # Read output line by line
            while True:
                output = process.stdout.readline()
                if output:
                    # Strip whitespace and add server prefix
                    output = output.strip()
                    if output:  # Only print non-empty lines
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[SERVER] [{timestamp}] {output}")
                        sys.stdout.flush()
                
                # Check if process has ended
                if process.poll() is not None:
                    # Read any remaining output
                    remaining_output = process.stdout.read()
                    if remaining_output:
                        for line in remaining_output.splitlines():
                            if line.strip():
                                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                print(f"[SERVER] [{timestamp}] {line.strip()}")
                                sys.stdout.flush()
                    
                    log(f"Server process ended with return code: {process.returncode}")
                    break

            log("Restarting server immediately...")

        except Exception as e:
            log(f"Error in monitor_server: {e}")
            import traceback
            traceback.print_exc()
            continue

if __name__ == "__main__":
    log("Admin monitor starting...")
    monitor_server() 