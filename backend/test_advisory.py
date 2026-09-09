import requests
import json
import time

URL = "http://localhost:8000/api/advisory"

def run_test():
    payload = {
        "nNDVI": 0.35,
        "lbp_texture_score": 0.82,
        "capacitance": 25.0,
        "acoustic_score": 55.0,
        "lat": 11.0,
        "lng": 77.0
    }
    
    print(f"Sending POST request to {URL} with payload:")
    print(json.dumps(payload, indent=2))
    print("-" * 50)
    
    try:
        response = requests.post(URL, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        print("Response received successfully!")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Failed to post to API: {e}")
        try:
            print("Response text:", response.text)
        except:
            pass

if __name__ == "__main__":
    run_test()
