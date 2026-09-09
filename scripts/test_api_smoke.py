import subprocess
import time
import requests
import sys

print("🚀 Starting FastAPI backend smoke test...")

# Boot backend
process = subprocess.Popen([sys.executable, "-m", "uvicorn", "GlobalPlantHealth.backend.main:app", "--port", "8008"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(3) # allow startup

tests_passed = 0
try:
    print("\n--- Test 1: Hit Root Interface ---")
    resp = requests.get("http://localhost:8008/")
    if resp.status_code == 200:
        print("✅ Root endpoint ALIVE!")
        tests_passed += 1
    
    print("\n--- Test 2: Deliberate Bad Request (Missing Params) ---")
    resp = requests.get("http://localhost:8008/api/inspect")
    if resp.status_code == 422: # Unprocessable Entity
        print("✅ Correctly rejected invalid params with 422.")
        tests_passed += 1
    else:
        print(f"❌ Failed to catch invalid params. Got {resp.status_code}")
        
    print("\n--- Test 3: Standard Request (Mocked Lat/Lng) ---")
    # This will fail with 500 since Gemini Key is missing in CI by default, which is expected
    resp = requests.get("http://localhost:8008/api/inspect", params={"lat": 13.0, "lng": 80.0})
    if resp.status_code == 500 and "Failed connecting to Gemini Engine" in resp.text:
        print("✅ Properly caught unauthenticated downstream Gemini exception (Expected without CI keys).")
        tests_passed += 1
    elif resp.status_code == 200:
        print("✅ Downstream APIs returned 200.")
        tests_passed += 1
    else:
        print(f"❌ Unexpected behavior on API inspect: {resp.status_code}")
        
except Exception as e:
    print(f"❌ Test framework crashed: {e}")
finally:
    process.terminate()
    print("\n🛑 Backend shut down.")

if tests_passed == 3:
    print("ALL TESTS PASSED!")
    sys.exit(0)
else:
    print("TESTS FAILED!")
    sys.exit(1)
