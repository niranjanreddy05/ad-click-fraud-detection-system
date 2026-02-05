"""
Startup script for Ad Click Fraud Detection System with Keras support
"""
import uvicorn
from main import app

if __name__ == "__main__":
    print("Starting Ad Click Fraud Detection System...")
    print("User Platform: http://127.0.0.1:8001")
    print("Advertiser Dashboard: http://127.0.0.1:8001/advertiser")
    print("API Docs: http://127.0.0.1:8001/docs")
    print()
    
    uvicorn.run(app, host="127.0.0.1", port=8001)