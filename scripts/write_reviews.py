import os

base = r"C:\Users\PRIYANRAJ J\.gemini\antigravity\scratch\smart-plant-health-monitoring-using-solar-images"
dirs = [
    "hardware/schematic",
    "docs/review-1",
    "docs/review-2",
    "docs/review-3",
    "docs/literature",
    "media"
]

for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

files = {
    "hardware/schematic/wiring-diagram.txt": "Label: Real Schematic/Wiring pending completion in Fritzing/KiCad. To be uploaded.",
    "docs/review-1/literature-survey.md": "Review 1 - Literature Survey completed here.",
    "docs/review-1/methodology.md": "Review 1 - Methodology notes.",
    "docs/review-1/simulation-model-30.md": "Review 1 - Simulation Model (30%).",
    "docs/review-2/simulation-model-60.md": "Review 2 - Simulation Model (60%).",
    "docs/review-3/simulation-model-100.md": "Review 3 - Final Simulation Models.",
    "docs/architecture.md": "# SATELLITE/MACRO LAYER vs GROUND HARDWARE\n\nGround Hardware is completely offline and handles localized real-time execution.\nThe Satellite layer described in this repo serves as an optional macroscopic screening tool.",
    "docs/novelty.md": "# Novelty Claims\n\n1. Use of a regressive RGB-to-NDVI proxy avoiding standard RGB limits.\n2. LBP texture anomaly filtering.\n3. Rolling temporal baselines to compute sudden drop-offs."
}

for fp, c in files.items():
    with open(os.path.join(base, fp), "w") as f:
        f.write(c)

print("Checklist updated.")
