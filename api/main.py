import os

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, create_model

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")

model_bundle = joblib.load(MODEL_PATH)
model = model_bundle["model"]
model_name = model_bundle["model_name"]
feature_order = model_bundle["feature_order"]
label_encoder = model_bundle["label_encoder"]

PatientFeatures = create_model(
    "PatientFeatures",
    **{gene: (float, ...) for gene in feature_order},
)


class PredictionResponse(BaseModel):
    predicted_subtype: str
    probabilities: dict[str, float]
    model_name: str


app = FastAPI(
    title="TCGA-BRCA Molecular Subtype Classifier API",
    description=(
        "Predicts PAM50 molecular subtype (Basal, Her2, LumA, LumB, Normal) "
        "from gene expression z-scores across the 50-gene PAM50 panel."
    ),
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "TCGA-BRCA subtype classifier API",
        "model": model_name,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/features")
def features():
    return {"feature_order": feature_order, "n_features": len(feature_order)}


@app.post("/predict", response_model=PredictionResponse)
def predict(patient: PatientFeatures):
    X = pd.DataFrame([patient.model_dump()])[feature_order]
    predicted_idx = model.predict(X)[0]
    predicted_proba = model.predict_proba(X)[0]

    return PredictionResponse(
        predicted_subtype=label_encoder.inverse_transform([predicted_idx])[0],
        probabilities={
            class_name: float(prob)
            for class_name, prob in zip(label_encoder.classes_, predicted_proba)
        },
        model_name=model_name,
    )
