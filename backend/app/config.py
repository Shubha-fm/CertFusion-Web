from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = Path(os.getenv('CERTFUSION_MODEL_PATH', ROOT / 'backend' / 'model_artifacts' / 'certfusion.pt'))
MODE = os.getenv('CERTFUSION_MODE', 'auto').lower()  # auto | demo | model
EPSILON = float(os.getenv('CERTFUSION_EPSILON', '0.031'))
CONFORMAL_ALPHA = float(os.getenv('CERTFUSION_ALPHA', '0.10'))
MAX_UPLOAD_MB = int(os.getenv('CERTFUSION_MAX_UPLOAD_MB', '80'))
TLC_JAR = os.getenv('TLC_JAR', '')
