import uuid
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Manim Renderer")

RENDERS_DIR = Path("renders")
RENDERS_DIR.mkdir(exist_ok=True)
app.mount("/renders", StaticFiles(directory="renders"), name="renders")

QUALITY_FLAGS = {"l": "-ql", "m": "-qm", "h": "-qh", "k": "-qk"}

class CodePayload(BaseModel):
    code: str
    quality: str = "m"


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = Path("index.html")
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    raise HTTPException(status_code=404, detail="index.html not found")


@app.post("/render")
async def render(payload: CodePayload):
    job_id = str(uuid.uuid4())
    work_dir = Path(tempfile.mkdtemp(prefix=f"manim_{job_id}_"))
    try:
        quality = payload.quality if payload.quality in QUALITY_FLAGS else "m"
        scene_file = work_dir / "scene.py"
        scene_file.write_text(payload.code)

        scene_name = _detect_scene_name(payload.code)
        if scene_name is None:
            raise HTTPException(
                status_code=422,
                detail="No Scene subclass found. Your class must inherit from Scene (or MovingCameraScene, ThreeDScene, etc.)."
            )

        cmd = [
            "manim", QUALITY_FLAGS[quality],
            "--media_dir", str(work_dir / "media"),
            "--disable_caching",
            str(scene_file), scene_name,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=str(work_dir))

        if result.returncode != 0:
            raise HTTPException(status_code=422, detail=(result.stderr or result.stdout or "Unknown error").strip())

        mp4_files = list((work_dir / "media").rglob("*.mp4"))
        if not mp4_files:
            raise HTTPException(status_code=500, detail="Manim succeeded but produced no MP4.")

        out_path = RENDERS_DIR / f"{job_id}.mp4"
        shutil.copy2(mp4_files[0], out_path)
        return {"job_id": job_id, "url": f"/renders/{job_id}.mp4", "scene": scene_name}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Render timed out after 120 seconds.")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def _detect_scene_name(code: str):
    import ast
    SCENE_BASES = {"Scene", "MovingCameraScene", "ThreeDScene", "ZoomedScene", "VectorScene", "GraphScene"}
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise HTTPException(status_code=422, detail=f"Syntax error: {exc}")
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                name = base.id if isinstance(base, ast.Name) else (base.attr if isinstance(base, ast.Attribute) else "")
                if name in SCENE_BASES:
                    return node.name
    return None


@app.delete("/renders/{job_id}")
async def delete_render(job_id: str):
    path = RENDERS_DIR / f"{job_id}.mp4"
    if path.exists():
        path.unlink()
        return {"deleted": job_id}
    raise HTTPException(status_code=404, detail="Not found.")