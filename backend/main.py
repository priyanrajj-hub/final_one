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

class CropRequest(BaseModel):
    tags: dict
    lat: float
    lng: float

class AdvisoryRequest(BaseModel):
    nNDVI: float
    lbp_texture_score: float
    capacitance: float
    acoustic_score: float
    lat: float
    lng: float
    
@app.post("/api/crop-inference")
def compute_crop_inference(req: CropRequest):
    result = infer_crop_type(req.tags, req.lat, req.lng)
    prov = "OSM Explicit Tag" if any("OSM" in k for k in result.keys()) else "Inferred from Geo-Heuristics"
    return {"ranked_crops": result, "provenance": prov}

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
