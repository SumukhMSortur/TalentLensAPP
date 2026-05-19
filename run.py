"""
TalentLens AI — Run this file to start the application.

Open http://127.0.0.1:8000/app/ in your browser after running.
"""

import uvicorn

if __name__ == "__main__":
    print("\n  TalentLens AI starting...")
    print("  Open http://127.0.0.1:8000/app/ in your browser\n")
    uvicorn.run(
        "backend.server:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
