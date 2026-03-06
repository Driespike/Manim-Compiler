# 🎬 Manim Compiler

A browser-based tool for writing, running, and downloading [Manim](https://www.manim.community/) animations — no local installation required. Paste your Python scene code, hit **Run**, and get back a rendered MP4 in seconds.

---

## ✨ Features

- **Live code editor** with tab-key support and syntax-friendly textarea
- **Auto scene detection** — the backend finds your `Scene` subclass automatically
- **Inline video playback** — watch the rendered animation right in the browser
- **One-click download** of the output MP4
- **Detailed error output** — Manim's full stderr is surfaced in the UI if rendering fails
- **Keyboard shortcut** `Ctrl / Cmd + Enter` to trigger a render
- **Load Example** button with a working Circle → Square animation to get started fast

---

## 🛠 Tech Stack

| Layer    | Technology                     |
|----------|-------------------------------|
| Backend  | Python · FastAPI · Uvicorn    |
| Renderer | Manim Community Edition       |
| Frontend | Vanilla HTML · CSS · JavaScript |

---

## 📁 Project Structure

```
Manim-Compiler/
├── main.py       # FastAPI app — render endpoint, file serving, cleanup
├── index.html    # Single-file frontend (served by FastAPI)
├── .gitignore
└── outputs/      # Auto-created at runtime — stores rendered MP4s
```

---

## 🚀 Getting Started

### 1. Install system dependencies

**Ubuntu / Debian**
```bash
sudo apt update && sudo apt install -y ffmpeg python3-pip
```

**macOS (Homebrew)**
```bash
brew install ffmpeg
```

> LaTeX support (for `MathTex`, `Tex`, etc.) requires a full LaTeX installation such as `texlive-full`.

---

### 2. Set up a Python environment

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install fastapi "uvicorn[standard]" manim
```

---

### 3. Run the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** — the frontend is served directly by FastAPI.

---

## 🎨 Usage

1. Paste your Manim scene code into the editor (or click **Load Example**).
2. *(Optional)* Enter your **Scene class name** in the field above the editor — leave it blank for auto-detection.
3. Click **▶ Run** or press **Ctrl/Cmd + Enter**.
4. The rendered animation plays inline. Hit **⬇ Download** to save the MP4.

### Example scene

```python
from manim import *

class CircleToSquare(Scene):
    def construct(self):
        circle = Circle(color=YELLOW, fill_opacity=0.3)
        square = Square(color=BLUE, fill_opacity=0.3)

        self.play(Create(circle))
        self.wait(0.5)
        self.play(Transform(circle, square), run_time=1.5)
        self.wait(1)
```

---

## 🔌 API Reference

### `POST /render`

Renders a Manim scene and returns a video URL.

**Request body**
```json
{
  "code": "from manim import *\n\nclass MyScene(Scene):\n    def construct(self):\n        ...",
  "scene_name": "MyScene"
}
```
`scene_name` is optional — omit it to auto-detect the first `Scene` subclass.

**Success `200`**
```json
{
  "success": true,
  "scene": "MyScene",
  "video_url": "/outputs/abc123_MyScene.mp4",
  "filename": "abc123_MyScene.mp4"
}
```

**Error `422`**
```json
{
  "detail": {
    "error": "Manim render failed.",
    "details": "... full stderr output ..."
  }
}
```

### `GET /outputs/{filename}`
Streams a rendered MP4 file.

### `DELETE /outputs/{filename}`
Deletes a rendered MP4 from the server.

---

## ⚙️ Configuration

| Setting | Default | Where to change |
|---------|---------|-----------------|
| Render quality | Low (`-ql`, 480p 15fps) | Change `"-ql"` to `"-qh"` (1080p) in `main.py` |
| Render timeout | 120 seconds | `timeout=120` in `main.py` |
| Output directory | `./outputs/` | `OUTPUT_DIR` constant in `main.py` |

> Rendered files in `outputs/` are **not** automatically purged. Call `DELETE /outputs/{filename}` or add a cron job to clean up periodically.

---

## 📄 License

MIT — feel free to use, modify, and distribute.
