from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uvicorn
from pydantic import BaseModel
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "sample_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS fields
                 (id INTEGER PRIMARY KEY, lat REAL, lng REAL, node_id TEXT, 
                  nNDVI_score REAL, texture_anomaly REAL, temporal_change REAL, 
                  fused_risk REAL, status TEXT)''')
    
    # Initialize with sample data if empty (since no live creds)
    c.execute("SELECT COUNT(*) FROM fields")
    if c.fetchone()[0] == 0:
        c.execute("""INSERT INTO fields (lat, lng, node_id, nNDVI_score, texture_anomaly, temporal_change, fused_risk, status)
                     VALUES (11.0, 77.0, 'NODE_01', 0.65, 0.1, 0.05, 0.15, 'HEALTHY_SAMPLE')""")
        c.execute("""INSERT INTO fields (lat, lng, node_id, nNDVI_score, texture_anomaly, temporal_change, fused_risk, status)
                     VALUES (11.01, 77.02, 'NODE_02', 0.40, 0.8, 0.9, 0.85, 'STRESS_SAMPLE')""")
        conn.commit()
    conn.close()

init_db()

@app.get("/")
def read_root():
    return {"status": "Backend Live (Sample Mode Enabled)"}

@app.get("/api/fields")
def get_fields():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, lat, lng, node_id, nNDVI_score, texture_anomaly, temporal_change, fused_risk, status FROM fields")
    rows = c.fetchall()
    conn.close()
    
    fields = []
    for r in rows:
        fields.append({
            "id": r[0], "lat": r[1], "lng": r[2], "node_id": r[3],
            "nNDVI_score": r[4], "texture_anomaly": r[5], "temporal_change": r[6],
            "fused_risk": r[7], "status": r[8]
        })
    return {"fields": fields, "data_source": "STATIC_SAMPLE (No Live API Credentials)"}

from algorithm.crop_inference import infer_crop_type

from typing import Optional, Dict, Any, List

class CropRequest(BaseModel):
    tags: Optional[Dict[str, Any]] = None
    lat: float
    lng: float
    ndvi_history: Optional[List[float]] = None
    area: Optional[float] = None
    log_correction: Optional[bool] = None
    crop: Optional[str] = None

class AdvisoryRequest(BaseModel):
    nNDVI: float
    lbp_texture_score: float
    capacitance: float
    acoustic_score: float
    lat: float
    lng: float
    
from fastapi import Request
import json

@app.post("/api/crop-inference")
async def compute_crop_inference(req: Request):
    try:
        body = await req.json()
    except:
        body_text = await req.body()
        try:
            body = json.loads(body_text)
        except:
            body = {}
            
    lat = body.get("lat", 0.0)
    lng = body.get("lng", 0.0)
    tags = body.get("tags", {})
    
    if body.get("log_correction"):
        return {"status": "saved"}
        
    result = infer_crop_type(tags, lat, lng)
    prov = "OSM Explicit Tag" if any("OSM" in k for k in result.keys()) else "Inferred from Geo-Heuristics"
    return {"ranked_crops": result, "provenance": prov, "best_guess": list(result.keys())[0] if result else "Unknown", "confidence": list(result.values())[0] if result else 0}

@app.post("/api/osm-lookup")
async def osm_lookup(req: Request):
    # Mocking standard landuse to prevent frontend error if the original external api isn't wired
    return {"elements": [{"tags": {"landuse": "farmland"}}]}

from llm_advisor import get_advisory

@app.post("/api/advisory")
def generate_advisory(req: AdvisoryRequest):
    sensor_data = {
        "nNDVI": req.nNDVI,
        "lbp_texture_score": req.lbp_texture_score,
        "capacitance": req.capacitance,
        "acoustic_score": req.acoustic_score
    }
    return get_advisory(sensor_data)

from fastapi import Request

@app.post("/api/gemini")
async def gemini_proxy(req: Request):
    data = await req.json()
    try:
        prompt_text = data.get("contents", [{}])[0].get("parts", [{}])[0].get("text", "")
    except Exception:
        return {"error": {"message": "Invalid request format"}}
        
    import google.generativeai as genai
    import os
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        return {"error": {"message": "API Key missing, triggering fallback"}}
    
    try:
        genai.configure(api_key=API_KEY.strip('\\').strip())
        model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt_text)
        return {"text": response.text}
    except Exception as e:
        return {"error": {"message": str(e)}}

from ml_pipeline import online_model

class MLPredictRequest(BaseModel):
    nNDVI: float
    lbp_texture_score: float
    capacitance: float
    acoustic_score: float

class MLFeedbackRequest(BaseModel):
    nNDVI: float
    lbp_texture_score: float
    capacitance: float
    acoustic_score: float
    true_label: str

@app.post("/api/ml-predict")
def ml_predict(req: MLPredictRequest):
    features = [req.nNDVI, req.lbp_texture_score, req.capacitance, req.acoustic_score]
    pred, conf = online_model.predict(features)
    return {"prediction": pred, "confidence": conf}

@app.post("/api/ml-feedback")
def ml_feedback(req: MLFeedbackRequest):
    features = [req.nNDVI, req.lbp_texture_score, req.capacitance, req.acoustic_score]
    status = online_model.feedback(features, req.true_label)
    return status

@app.get("/api/ml-status")
def ml_status():
    return online_model.get_status()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
