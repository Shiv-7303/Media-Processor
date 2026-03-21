# Media Processor

A full-stack media processing app — paste a video URL, pick an operation, get the result.

**Stack:** Python (Flask) · HTML/CSS/JS · FFmpeg via subprocess

---

## Folder Structure

```
media-processor/
├── backend/
│   ├── app.py              ← Flask API
│   ├── requirements.txt    ← dependencies
│   └── outputs/            ← processed files saved here
├── frontend/
│   └── index.html          ← UI (open in browser)
└── README.md
```

---

## Prerequisites

- Python 3.8+
- FFmpeg in system PATH
- pip

**Install FFmpeg:**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

---

## Run the Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```
Runs at: `http://localhost:5000`

## Open the Frontend

Open `frontend/index.html` directly in your browser. No build step needed.

---

## API Reference

### POST /process

**Request:**
```json
{ "url": "https://example.com/video.mp4", "operation": "thumbnail" }
```

| Operation | Output |
|---|---|
| `thumbnail` | JPG frame at 2s |
| `compress` | H.264 compressed MP4 |
| `extract_audio` | MP3 audio file |

**Success:**
```json
{ "status": "success", "output": "/output/abc123.jpg" }
```

**Error:**
```json
{ "status": "error", "message": "FFmpeg failed: ..." }
```

### GET /output/<filename>
Serves processed file directly.

---

## Test URL (sample)

```
https://www.w3schools.com/html/mov_bbb.mp4
```

---

## Assumptions

- Input must be a direct video URL (HTTP/HTTPS)
- Input file deleted after processing; output persists in `outputs/`
- Frontend talks to backend at `http://localhost:5000`