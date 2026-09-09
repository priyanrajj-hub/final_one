from http.server import BaseHTTPRequestHandler
import json
import os
import io

try:
    import ee
except ImportError:
    ee = None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if not ee:
                raise Exception("earthengine-api is not installed or failed to load on Vercel.")

            creds_json_str = os.environ.get('GEE_SERVICE_ACCOUNT_JSON')
            if not creds_json_str:
                raise Exception("Missing GEE_SERVICE_ACCOUNT_JSON environment variable. Please add it to Vercel Settings.")
            
            creds_dict = json.loads(creds_json_str)
            
            # Using google.oauth2.service_account which is modern and what GEE expects
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            ee.Initialize(credentials)

            # Test simple point query for Dynamic World
            # Coordinates for somewhere in Punjab
            point = ee.Geometry.Point([75.0, 30.0])
            
            # Filter DW collection for the point
            dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1") \
                .filterBounds(point) \
                .sort('system:time_start', False) \
                .first()
            
            # Extract probability array for the first image
            probs = dw.select(['water', 'trees', 'grass', 'flooded_vegetation', 'crops', 'shrub_and_scrub', 'built', 'bare', 'snow_and_ice'])
            stats = probs.reduceRegion(reducer=ee.Reducer.first(), geometry=point, scale=10).getInfo()
            date_ms = dw.get('system:time_start').getInfo()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True, 
                "message": "Authenticated correctly!",
                "data": stats,
                "latest_date_ms": date_ms
            }).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
