from pathlib import Path
import os
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.main import app

DIST = Path(__file__).resolve().parent / 'frontend_dist'

if DIST.exists():
    app.mount('/assets', StaticFiles(directory=DIST / 'assets'), name='assets')

    @app.get('/{full_path:path}', include_in_schema=False)
    def spa(full_path: str):
        target = DIST / full_path
        if target.is_file():
            return FileResponse(target)
        return FileResponse(DIST / 'index.html')

if __name__ == '__main__':
    # Hugging Face Docker Spaces expose port 7860 by default.
    # PORT can still override this for other platforms.
    port = int(os.environ.get('PORT', '7860'))
    uvicorn.run(app, host='0.0.0.0', port=port)
