"""
Sends one real patient (from data/brca_pam50_dataset.csv) to a locally running
instance of the API and prints the prediction.

Usage:
    uvicorn main:app --reload   # in one terminal, from the api/ folder
    python test_api.py          # in another terminal, from the api/ folder
"""

import json

import pandas as pd
import requests

API_URL = "http://127.0.0.1:8000/predict"
DATA_PATH = "../data/brca_pam50_dataset.csv"

feature_order = requests.get("http://127.0.0.1:8000/features").json()["feature_order"]

dataset = pd.read_csv(DATA_PATH)
sample = dataset.iloc[0]
payload = {gene: float(sample[gene]) for gene in feature_order}

response = requests.post(API_URL, json=payload)
result = response.json()

print(f"True subtype:      {sample['SUBTYPE']}")
print(f"Predicted subtype: {result['predicted_subtype']}")
print("Class probabilities:")
print(json.dumps(result["probabilities"], indent=2))
