from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any
import os
import uuid

from database import (
    init_database, insert_sample_data, get_ads, log_click,
    get_advertiser_stats, get_recent_clicks, create_advertiser,
    authenticate_advertiser, create_ad,
    get_advertiser_ads, get_ad_with_advertiser
)
from feature_builder import FeatureBuilder
from keras_loader import load_keras_model_safe

# -------------------- FASTAPI APP --------------------

app = FastAPI(title="Ad Click Fraud Detection API", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- GLOBALS --------------------

model = {
    "classifier": None,
    "scaler": None
}

model_name = None
sessions = {}


def load_model():
    global model, model_name

    try:
        print("Loading ML model and preprocessor...")

        # Load ANN model and preprocessor
        classifier = load_keras_model_safe("training/ann_click_fraud_model.h5")
        scaler = joblib.load("training/ann_preprocessor.pkl")

        if classifier is None:
            raise RuntimeError("Failed to load ANN model")

        # ANN model input shape check (optional, handled by keras)
        # print(f"Model expects {classifier.input_shape} features")

        model["classifier"] = classifier
        model["scaler"] = scaler

        model_name = "ANN Click Fraud Detection Model"

        print("SUCCESS: Model loaded correctly")

    except Exception as e:
        print("ERROR loading model:", e)
        raise RuntimeError("Model loading failed")


# -------------------- SCHEMAS --------------------

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class CreateAdRequest(BaseModel):
    title: str
    description: str
    image_url: str
    target_url: str

class ClickData(BaseModel):
    session_id: str
    clicks_per_session: int
    time_gap_seconds: float
    session_duration_minutes: float
    ad_id: int
    user_agent_category: int = 1

class PredictionResponse(BaseModel):
    is_fraud: bool
    fraud_probability: float
    risk_level: str
    model_used: str

# -------------------- HELPERS --------------------


def get_risk_level(prob: float) -> str:
    if prob < 0.1:
        return "Low"
    elif prob < 0.8:
        return "Medium"
    else:
        return "High"


def get_current_advertiser(request: Request):
    session_id = request.cookies.get("session_id")
    print(f"Session ID from cookie: {session_id}")
    if not session_id or session_id not in sessions:
        print(f"Authentication failed. Available sessions: {list(sessions.keys())}")
        raise HTTPException(status_code=401, detail="Not authenticated")
    advertiser = sessions[session_id]
    print(f"Current advertiser: {advertiser}")
    return advertiser

# -------------------- STARTUP --------------------

@app.on_event("startup")
async def startup_event():
    print("Starting application...")
    os.makedirs("models", exist_ok=True)
    load_model()
    init_database()
    insert_sample_data()
    print("Startup complete")

# -------------------- ROUTES --------------------

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("user_dashboard.html", {"request": request})

@app.post("/auth/signup")
async def signup(data: SignupRequest, response: Response):
    advertiser_id = create_advertiser(data.name, data.email, data.password)
    if advertiser_id is None:
        raise HTTPException(400, "Email already registered")

    session_id = str(uuid.uuid4())
    sessions[session_id] = {"id": advertiser_id, "name": data.name, "email": data.email}

    response.set_cookie("session_id", session_id, httponly=True)
    return {"message": "Signup successful"}

@app.post("/auth/login")
async def login(data: LoginRequest, response: Response):
    advertiser = authenticate_advertiser(data.email, data.password)
    if not advertiser:
        raise HTTPException(401, "Invalid credentials")

    session_id = str(uuid.uuid4())
    sessions[session_id] = advertiser
    response.set_cookie("session_id", session_id, httponly=True)
    return {"message": "Login successful"}


@app.post("/predict", response_model=PredictionResponse)
async def predict(click: ClickData):

    if model["classifier"] is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    ad_info = get_ad_with_advertiser(click.ad_id)
    if not ad_info:
        raise HTTPException(status_code=404, detail="Ad not found")

    classifier = model["classifier"]
    scaler = model["scaler"]

    # Build features using FeatureBuilder
    X = FeatureBuilder.build(click)

    # Preprocess features
    X_processed = scaler.transform(X)

    # Predict
    fraud_prob = float(classifier.predict(X_processed)[0][0])
    fraud_prob = max(fraud_prob, 0.001)

    is_fraud = fraud_prob >= 0.5
    risk = get_risk_level(fraud_prob)

    log_click(
        ad_id=click.ad_id,
        advertiser_id=ad_info["advertiser_id"],
        session_id=click.session_id,
        clicks_per_session=click.clicks_per_session,
        time_gap_seconds=click.time_gap_seconds,
        session_duration_minutes=click.session_duration_minutes,
        user_agent_category=click.user_agent_category,
        is_fraud=is_fraud,
        fraud_probability=fraud_prob,
        risk_level=risk,
        model_used=model_name
    )

    return PredictionResponse(
        is_fraud=is_fraud,
        fraud_probability=fraud_prob,
        risk_level=risk,
        model_used=model_name
    )


@app.get("/health")
async def health():
    return {
        "status": "running",
        "model_loaded": model["classifier"] is not None,
        "model_name": model_name
    }

@app.get("/login")
async def login_page(request: Request):
    """Serve the login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup")
async def signup_page(request: Request):
    """Serve the signup page"""
    return templates.TemplateResponse("signup.html", {"request": request})

# Authentication endpoints
@app.post("/auth/signup")
async def signup(signup_data: SignupRequest, response: Response):
    """Register new advertiser"""
    advertiser_id = create_advertiser(
        name=signup_data.name,
        email=signup_data.email,
        password=signup_data.password
    )

    if advertiser_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create session
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": advertiser_id,
        "name": signup_data.name,
        "email": signup_data.email
    }

    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=86400  # 24 hours
    )

    return {"message": "Account created successfully", "advertiser_id": advertiser_id}

@app.post("/auth/login")
async def login(login_data: LoginRequest, response: Response):
    """Authenticate advertiser"""
    advertiser = authenticate_advertiser(login_data.email, login_data.password)

    if not advertiser:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create session
    session_id = str(uuid.uuid4())
    sessions[session_id] = advertiser

    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=86400  # 24 hours
    )

    return {"message": "Login successful", "advertiser": advertiser}

@app.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout advertiser"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]

    response.delete_cookie("session_id")
    return {"message": "Logged out successfully"}

@app.get("/auth/me")
async def get_current_user(advertiser: Dict[str, Any] = Depends(get_current_advertiser)):
    """Get current advertiser info"""
    return advertiser

# Ad management endpoints
@app.post("/ads/create")
async def create_new_ad(
    ad_data: CreateAdRequest,
    advertiser: Dict[str, Any] = Depends(get_current_advertiser)
):
    """Create new ad for authenticated advertiser"""
    ad_id = create_ad(
        advertiser_id=advertiser["id"],
        title=ad_data.title,
        description=ad_data.description,
        image_url=ad_data.image_url,
        target_url=ad_data.target_url
    )

    return {"message": "Ad created successfully", "ad_id": ad_id}

@app.get("/ads/my-ads")
async def get_my_ads(advertiser: Dict[str, Any] = Depends(get_current_advertiser)):
    """Get all ads for authenticated advertiser"""
    ads = get_advertiser_ads(advertiser["id"])
    return {"ads": ads}

@app.get("/ads/active")
async def get_active_ads():
    """Get all active ads for user platform (no auth required)"""
    try:
        ads = get_ads()
        return {"ads": ads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/health")
async def health_check():
    """API health check endpoint"""
    return {
        "message": "Ad Click Fraud Detection API",
        "status": "running",
        "model_loaded": model["classifier"] is not None,
        "model_name": model_name
    }



@app.get("/model/info")
async def model_info():
    classifier = model["classifier"]
    return {
        "model_name": model_name,
        "model_type": type(classifier).__name__,
        "features_expected": classifier.input_shape[1] if hasattr(classifier, "input_shape") else "Unknown"
    }


@app.get("/ads")
async def get_all_ads():
    """Get all active ads for display (deprecated - use /ads/active)"""
    try:
        ads = get_ads()
        return {"ads": ads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/advertiser/{advertiser_id}/stats")
async def get_stats(
    advertiser_id: int,
    advertiser: Dict[str, Any] = Depends(get_current_advertiser)
):
    """Get click statistics for authenticated advertiser"""
    # Ensure advertiser can only access their own stats
    if advertiser["id"] != advertiser_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    try:
        stats = get_advertiser_stats(advertiser_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/advertiser")
async def advertiser_dashboard(request: Request):
    """Serve the advertiser dashboard"""
    return templates.TemplateResponse("advertiser_dashboard.html", {"request": request})

@app.get("/advertiser/{advertiser_id}/clicks")
async def get_clicks(
    advertiser_id: int,
    limit: int = 50,
    advertiser: Dict[str, Any] = Depends(get_current_advertiser)
):
    """Get recent clicks for authenticated advertiser"""
    # Ensure advertiser can only access their own clicks
    if advertiser["id"] != advertiser_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    try:
        print(f"Loading sessions for advertiser_id: {advertiser_id}")
        clicks = get_recent_clicks(advertiser_id, limit)
        print(f"Found {len(clicks)} sessions for advertiser {advertiser_id}")
        return {"clicks": clicks}
    except Exception as e:
        print(f"Error in get_clicks: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
