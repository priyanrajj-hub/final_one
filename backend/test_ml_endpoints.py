import requests
import json
import time

BASE = "http://localhost:8000/api"

print("Fetching initial ml-status...")
try:
    res = requests.get(f"{BASE}/ml-status")
    print("Initial:", res.json())
except Exception as e:
    print(f"Error, is the server running? {e}")
    exit(1)

# We will simulate 3 targeted feedback loops designed to sway the model's accuracy
feedbacks = [
    {"nNDVI": 0.8, "lbp_texture_score": 0.1, "capacitance": 0.9, "acoustic_score": 0.05, "true_label": "Healthy"},
    {"nNDVI": 0.3, "lbp_texture_score": 0.2, "capacitance": 0.1, "acoustic_score": 0.01, "true_label": "Drought"},
    {"nNDVI": 0.45, "lbp_texture_score": 0.8, "capacitance": 0.6, "acoustic_score": 0.9, "true_label": "Pest"}
]

print("\nExecuting 3 consecutive ml-feedback calls...")
for i, f in enumerate(feedbacks, start=1):
    time.sleep(0.5)
    print(f"--- Feedback Call #{i} ---")
    print(f"Sending Ground Truth Data: {f}")
    res = requests.post(f"{BASE}/ml-feedback", json=f)
    print(f"Result Status: {res.json()}")
