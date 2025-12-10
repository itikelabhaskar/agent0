import socket
import subprocess
import sys
import os

def find_free_port(start_port=8080, max_port=8100):
    """Find a free port on localhost within the specified range."""
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No free ports found between {start_port} and {max_port}")

if __name__ == "__main__":
    try:
        port = find_free_port()
        print(f"Starting backend on port {port}")
        
        # Write port to a file so frontend can find it
        with open(".backend_port", "w") as f:
            f.write(str(port))
            
        # Run uvicorn
        cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", str(port)]
        subprocess.run(cmd)
        
    except Exception as e:
        print(f"Error starting backend: {e}")
        sys.exit(1)
