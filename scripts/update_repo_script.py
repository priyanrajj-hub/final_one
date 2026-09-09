import os
import subprocess

def run(cmd):
    print(">", cmd)
    try:
        out = subprocess.check_output(cmd, shell=True).decode('utf-8')
        print(out)
    except subprocess.CalledProcessError as e:
        print("ERROR:", e.output.decode('utf-8'))

run("git branch -a")

# Soft reset the last squashed commit to unstage files, so we can split them
# It assumes c7145a3e was HEAD, and we reset 1 step back. Let's do it based on message.
try:
    log_out = subprocess.check_output("git log -n 1 --oneline", shell=True).decode('utf-8')
    if "chore: Apply honesty labels" in log_out:
        run("git reset --soft HEAD~1")
        run("git restore --staged .")
        print("Soft reset successful.")
except Exception as e:
    print("Error formatting git:", e)

# 1. Rename write_reviews.py to scripts/write_reviews.py
os.makedirs("scripts", exist_ok=True)
if os.path.exists("write_reviews.py"):
    run("git rm --cached write_reviews.py")
    os.rename("write_reviews.py", "scripts/write_reviews.py")

# 2. Add LICENSE file (MIT)
with open("LICENSE", "w") as f:
    f.write('''MIT License

Copyright (c) 2026 Author

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
''')

# 3. Read README.md, fix naming, fix links, add badge
with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

# Fix naming inconsistency
readme = readme.replace('AGRISENSE — Field Intelligence Dashboard', 'Canopy: Global Vegetation Health Monitor')
# Replace dead 'offline companion repo' link with review2
readme = readme.replace('refer to the offline companion repo', 'refer to our [Hardware Validation Repo](https://github.com/priyanrajj-hub/review2)')

# Add Badge section at the top
badges = """
[![Vercel Deploy](https://img.shields.io/badge/Vercel-Deployed-success)](https://smart-plant-health-monitoring-using.vercel.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*Companion Hardware Research Repo:* [Review-2 Repository (Microwave Dielectric Leaf Sensing)](https://github.com/priyanrajj-hub/review2)

### Quick Run
```bash
npm install
node server.js
```

"""

if "Vercel Deploy" not in readme:
    readme = readme.replace('Canopy: Global Vegetation Health Monitor\n\n', 'Canopy: Global Vegetation Health Monitor\n\n' + badges)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

# Commit 1: Gemini payload fix
run("git add api/gemini.js")
run('git commit -m "fix: resolve Gemini payload format mismatch routing"')

# Commit 2: Open-Meteo rainfall integration & random removal
run("git add index.html")
run('git commit -m "feat: Open-Meteo rainfall integration & remove Math.random() mock data"')

# Commit 3: Smoke tests
run("git add test_smoke.js test_smoke_local.js")
run('git commit -m "test: Add local smoke tests for API and frontend resiliency"')

# Commit 4: Server fixes
run("git add server.js package.json")
run('git commit -m "fix: Resolve local dev server static routing"')

# Commit 5: Repository clean up (License, Readme, Scripts)
if os.path.exists("write_reviews.py"):
    run("git rm write_reviews.py")
run("git add README.md LICENSE scripts/write_reviews.py")
run('git commit -m "docs: Align README naming, list verifiable features, add MIT license & script dirs"')

run("git log -n 6 --oneline")
