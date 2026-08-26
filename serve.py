from pathlib import Path
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.main import app

DIST=Path(__file__).resolve().parent/'frontend_dist'
if DIST.exists():
    app.mount('/assets', StaticFiles(directory=DIST/'assets'), name='assets')
    @app.get('/{full_path:path}', include_in_schema=False)
    def spa(full_path:str):
        target=DIST/full_path
        if target.is_file(): return FileResponse(target)
        return FileResponse(DIST/'index.html')

if __name__=='__main__':
    uvicorn.run(app,host='0.0.0.0',port=8000)
