import os
from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    is_dev = os.environ.get("ENV", "development").lower() == "development" and "RENDER" not in os.environ

    app.run(
        host=host,
        port=port,
        debug=is_dev
    )
