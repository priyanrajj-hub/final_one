import urllib.request
import json
import traceback
import os

with open('diag_output.txt', 'w', encoding='utf-8') as f:
    def log(msg):
        print(msg)
        f.write(msg + '\n')

    def check_url(url, method='GET', data=None):
        try:
            req = urllib.request.Request(url, method=method, headers={'Content-Type': 'application/json'})
            if data:
                req.data = json.dumps(data).encode('utf-8')
            response = urllib.request.urlopen(req, timeout=10)
            body = response.read().decode('utf-8')
            log(f'URL: {url}')
            log(f'Status: {response.status}')
            log(f'Body: {body[:500]}')
            log('-'*40)
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8')
            log(f'URL: {url}')
            log(f'HTTP Error Status: {e.code}')
            log(f'Error Body: {body[:500]}')
            log('-'*40)
        except Exception as e:
            log(f'URL: {url} -> Fatal Error: {str(e)}')

    log('==== LIVE VERCEL DIAGNOSTICS ====')
    check_url('https://smart-plant-health-monitoring-using.vercel.app/api/health')
    check_url('https://smart-plant-health-monitoring-using.vercel.app/api/gemini', method='POST', data={'prompt': 'health check'})
    
    log('==== LOCAL CODE STATE ====')
    with open('index.html', 'r', encoding='utf-8') as html_file:
        html = html_file.read()
        log(f"CONFIDENCE BADGE: {'PRESENT' if 'id=\"confidence-badge\"' in html else 'MISSING'}")
        log(f"MOCK LABELS: {'PRESENT' if 'SAMPLE MOCK' in html else 'MISSING'}")
