from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import uuid
import requests as req

app = Flask(__name__)
CORS(app)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ALLOWED_OPS = ["thumbnail", "compress", "extract_audio"]


# ─── Helper: Download media from URL ─────────────────────────────────────────

def download_media(url, dest):
    try:
        r = req.get(url, stream=True, timeout=30)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    except req.exceptions.MissingSchema:
        raise ValueError("Invalid URL — check the format.")
    except req.exceptions.ConnectionError:
        raise ValueError("Could not connect to the URL.")
    except req.exceptions.HTTPError as e:
        raise ValueError(f"HTTP error: {e}")
    except req.exceptions.Timeout:
        raise ValueError("Download timed out (30s limit).")


# ─── Main endpoint ────────────────────────────────────────────────────────────

@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    print(">>> REQUEST AAYA", flush=True)  # ye add karo
    data = request.get_json()
    print(">>> DATA:", data, flush=True)   #

    # Validate request
    if not data:
        return jsonify({"status": "error", "message": "Request body must be JSON."}), 400

    url = data.get("url", "").strip()
    operation = data.get("operation", "").strip()

    if not url:
        return jsonify({"status": "error", "message": "URL is required."}), 400
    if not operation:
        return jsonify({"status": "error", "message": "Operation is required."}), 400
    if operation not in ALLOWED_OPS:
        return jsonify({"status": "error", "message": f"Invalid operation. Use: {', '.join(ALLOWED_OPS)}"}), 400

    uid = uuid.uuid4().hex
    input_path = os.path.join(OUTPUT_DIR, f"input_{uid}.mp4")
    output_path = None

    # Step 1 — Download
    try:
        download_media(url, input_path)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Download failed: {e}"}), 500

    try:
        # Step 2 — Build FFmpeg command
        if operation == "thumbnail":
            output_path = os.path.join(OUTPUT_DIR, f"{uid}.jpg")
            cmd = ["ffmpeg", "-i", input_path, "-ss", "00:00:02", "-vframes", "1", output_path, "-y"]

        elif operation == "compress":
            output_path = os.path.join(OUTPUT_DIR, f"{uid}_compressed.mp4")
            cmd = ["ffmpeg", "-i", input_path, "-vcodec", "libx264", "-crf", "28", "-preset", "fast", output_path, "-y"]

        elif operation == "extract_audio":
            output_path = os.path.join(OUTPUT_DIR, f"{uid}.mp3")
            cmd = ["ffmpeg", "-i", input_path,"-q:a", "0", "-map", "0:a:0", output_path, "-y"]
        # Step 3 — Run via subprocess (mandatory)
        result = subprocess.run(cmd, timeout=120, capture_output=True)
        print(">>> RETURNCODE:", result.returncode, flush=True)
        print(">>> FFMPEG STDERR:", result.stderr.decode("utf-8", errors="replace"), flush=True)

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")
            lines = [l for l in stderr.splitlines() if l.strip()]
            msg = lines[-1] if lines else "Unknown FFmpeg error"
            return jsonify({"status": "error", "message": f"FFmpeg failed: {msg}"}), 500

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            return jsonify({"status": "error", "message": "FFmpeg ran but output file is empty. Check input format."}), 500

        return jsonify({"status": "success", "output": f"/output/{os.path.basename(output_path)}"})

    except subprocess.TimeoutExpired:
        return jsonify({"status": "error", "message": "FFmpeg timed out (120s). Try a shorter/smaller file."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"Processing error: {e}"}), 500
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)


# ─── Serve output files ───────────────────────────────────────────────────────

@app.route("/output/<filename>")
def serve_output(filename):
    safe = os.path.basename(filename)
    path = os.path.join(OUTPUT_DIR, safe)
    if not os.path.exists(path):
        return jsonify({"error": "File not found."}), 404
    return send_file(path, as_attachment=True)


# ─── Health check ─────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)