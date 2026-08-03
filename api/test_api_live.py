"""
Same as test_api.py, but sends the request to the live Render deployment
instead of a local server. No need to have uvicorn running for this one.

Usage:
    python test_api_live.py

Note: Render's free tier spins the service down after inactivity — the first
request after idle time can take up to ~50 seconds while it wakes up.
"""

import json

import pandas as pd
import requests

BASE_URL = "https://tcga-brca-subtype-classifier.onrender.com"
DATA_PATH = "../data/brca_pam50_dataset.csv"

print("Contacting the live API (may take up to ~50s if it was asleep)...")

feature_order = requests.get(f"{BASE_URL}/features", timeout=90).json()["feature_order"]

dataset = pd.read_csv(DATA_PATH)
sample = dataset.iloc[0]
payload = {gene: float(sample[gene]) for gene in feature_order}

response = requests.post(f"{BASE_URL}/predict", json=payload, timeout=90)
result = response.json()

print(f"True subtype:      {sample['SUBTYPE']}")
print(f"Predicted subtype: {result['predicted_subtype']}")
print("Class probabilities:")
print(json.dumps(result["probabilities"], indent=2))
