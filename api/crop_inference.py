from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# Add parent directory to path to allow importing algorithm module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from algorithm.crop_inference import infer_crop_type
except Exception as e:
    # Just in case mapping fails in Vercel
    def infer_crop_type(*args, **kwargs):
        return {"best_guess": "Error", "confidence": 0, "shortlist": []}

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            # Handle logging corrections
            if data.get('log_correction') is True:
                crop = data.get('crop', 'Unknown')
                lat = data.get('lat', 0.0)
                lng = data.get('lng', 0.0)
                print(f"[CROP CORRECTION LOGGED] Location: {lat},{lng} | User Corrected To: {crop}")
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
                return

            lat = float(data.get('lat', 0.0))
            lng = float(data.get('lng', 0.0))
            tags = data.get('tags', {})
            ndvi_history = data.get('ndvi_history')
            area = float(data.get('area', -1.0))

            result = infer_crop_type(tags, lat, lng, ndvi_history, area)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
