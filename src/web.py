import os
from typing import TypedDict

from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
# from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import uvicorn

BASE_DIR = Path(__file__).parent

class FSItem(TypedDict):
    name: str
    path: str
    type: str

app = FastAPI()
# app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@app.get('/directory-browser')
async def directory_browser(request: Request):
    return templates.TemplateResponse('directory_browser.html', {"request": request})

@app.get('/api/directory')
async def get_directory(path: str = ''):
    if len(path) == 0:
        path = 'Y://'
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    
    items: list[FSItem] = []
    if os.path.exists(path):
        for entry in os.listdir(path):
            if entry.startswith('.') or entry.endswith('.json') or entry.startswith('_'):
                continue
            entry_path = os.path.join(path, entry)
            items.append({
                'name': entry,
                'path': entry_path,
                'type': 'directory' if os.path.isdir(entry_path) else 'file'
            })
    return JSONResponse(content=sorted(items, key=lambda x: x['name']))

@app.get('/api/file')
async def get_file(path: str):
    if not os.path.exists(path) or not os.path.isfile(path):
        raise HTTPException(status_code=404)
    
    if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        return FileResponse(path, media_type=f'image/{path.split(".")[-1]}')
    elif path.lower().endswith('.pdf'):
        return FileResponse(path, media_type='application/pdf')
    else:
        raise HTTPException(status_code=400, detail='Unsupported file type')

if __name__ == "__main__":
    uvicorn.run("web:app", host="127.0.0.1", port=8000, log_level="info")
