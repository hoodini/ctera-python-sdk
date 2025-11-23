from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yaml
import os
import json

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SETTINGS_PATH = os.path.join(BASE_DIR, "cterasdk", "settings.yml")
README_PATH = os.path.join(BASE_DIR, "README.md")

class SettingsUpdate(BaseModel):
    content: str

@app.get("/api/readme")
def get_readme():
    try:
        with open(README_PATH, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
def get_settings():
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
def update_settings(settings: SettingsUpdate):
    try:
        # Validate YAML
        try:
            yaml.safe_load(settings.content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")

        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            f.write(settings.content)
        return {"status": "success"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/file_structure")
def get_file_structure():
    # Return a simplified file structure for visualization
    structure = []
    for root, dirs, files in os.walk(os.path.join(BASE_DIR, "cterasdk")):
        if "__pycache__" in root:
            continue
        
        rel_root = os.path.relpath(root, BASE_DIR)
        files_list = [f for f in files if f.endswith('.py') or f.endswith('.yml')]
        
        if files_list:
            structure.append({
                "path": rel_root,
                "files": files_list
            })
    return structure

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

