import uvicorn
from app.app_p import app
from app.config import settings  

if __name__ == "__main__":
    uvicorn.run(
        "app.app_p:app",  
        host=getattr(settings, "app_host", "0.0.0.0"),  
        port=getattr(settings, "app_port", 8000),       
        reload=settings.debug,
    )