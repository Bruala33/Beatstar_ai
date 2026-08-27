import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    # In cloud environments (e.g. Render), disable reload unless ENV=development
    is_dev = os.environ.get("ENV", "development").lower() == "development" and "RENDER" not in os.environ

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=is_dev
    )
