"""
LexMetrix - Vercel Serverless Function Entrypoint
Exposes the FastAPI 'app' object for @vercel/python runtime.
"""
import sys
import os

# Inject repository root into Python module search path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Ensure VERCEL environment flag is set
os.environ["VERCEL"] = "1"

from backend.main import app
