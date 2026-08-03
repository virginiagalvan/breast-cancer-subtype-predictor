import io
import json
import os

import joblib
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field, create_model

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")
EXAMPLE_PATH = os.path.join(os.path.dirname(__file__), "example_patient.json")

model_bundle = joblib.load(MODEL_PATH)
model = model_bundle["model"]
model_name = model_bundle["model_name"]
feature_order = model_bundle["feature_order"]
label_encoder = model_bundle["label_encoder"]

with open(EXAMPLE_PATH) as f:
    example_patient = json.load(f)

GENE_DESCRIPTION = (
    "mRNA expression z-score relative to diploid samples (TCGA-BRCA PanCancer Atlas "
    "convention). Typical range: roughly -3 to 3."
)

PatientFeatures = create_model(
    "PatientFeatures",
    **{
        gene: (float, Field(..., description=f"{GENE_DESCRIPTION} Gene: {gene}."))
        for gene in feature_order
    },
)


class PredictionResponse(BaseModel):
    predicted_subtype: str = Field(
        ..., description="Predicted PAM50 molecular subtype: Basal, Her2, LumA, LumB, or Normal."
    )
    probabilities: dict[str, float] = Field(
        ..., description="Predicted probability for each of the 5 subtypes, summing to 1."
    )
    model_name: str = Field(..., description="Name of the underlying trained model.")


app = FastAPI(
    title="TCGA-BRCA Molecular Subtype Classifier API",
    description=(
        "Predicts PAM50 molecular subtype (Basal, Her2, LumA, LumB, Normal) from gene "
        "expression z-scores across the 50-gene PAM50 panel.\n\n"
        "**In a real deployment**, this API would be called by an upstream bioinformatics "
        "pipeline that processes raw sequencing data into normalized expression values — "
        "not filled in by hand. The endpoints below are set up so a person can still try the "
        "model directly from this page.\n\n"
        "**New here? Two ways to try it:**\n"
        "1. Single patient — call `GET /example`, copy its response body, paste it into "
        "`POST /predict` below.\n"
        "2. Multiple patients at once — call `POST /predict/csv` and upload a CSV file "
        "(one row per patient, one column per gene).\n\n"
        "**Input format:** each field/column is a gene symbol (see `GET /features` for the "
        "exact list) mapped to its mRNA expression z-score, computed relative to diploid "
        "samples — the same convention used by the TCGA-BRCA PanCancer Atlas study this "
        "model was trained on (via cBioPortal).\n\n"
        "Source code, training notebooks, and the full dataset: "
        "[github.com/virginiagalvan/tcga-brca-subtype-classifier]"
        "(https://github.com/virginiagalvan/tcga-brca-subtype-classifier)."
    ),
    version="1.0.0",
)


@app.get("/", summary="API info")
def root():
    return {
        "message": "TCGA-BRCA subtype classifier API",
        "model": model_name,
        "docs": "/docs",
        "quick_start": "Call GET /example for a ready-to-use sample request, then try POST /predict.",
    }


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


@app.get(
    "/features",
    summary="List expected input genes",
    description="Returns the 50 PAM50 gene symbols the model expects, in the exact order used during training.",
)
def features():
    return {"feature_order": feature_order, "n_features": len(feature_order)}


@app.get(
    "/example",
    summary="Get a ready-to-use example patient (single, JSON)",
    description=(
        "Returns one real patient's 50 gene expression z-scores, in the exact shape "
        "`POST /predict` expects — copy the **entire response body** and paste it directly "
        "into `/predict`'s request field, no editing needed. The patient's true PAM50 "
        "subtype is returned in the `X-True-Subtype` response header (not in the body), so "
        "the body itself stays copy-paste-ready."
    ),
)
def example(response: Response):
    response.headers["X-True-Subtype"] = example_patient["true_subtype"]
    return example_patient["features"]


@app.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict PAM50 subtype",
    description=(
        "Takes gene expression z-scores for the 50-gene PAM50 panel and returns the "
        "predicted molecular subtype with per-class probabilities. Don't have a sample "
        "handy? Call `GET /example` first and paste its `features` object here."
    ),
)
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


@app.post(
    "/predict/csv",
    summary="Predict PAM50 subtype for multiple patients (CSV upload)",
    description=(
        "Upload a CSV file with one row per patient and one column per gene (see "
        "`GET /features` for the required column names). An optional `SAMPLE_ID` or "
        "`PATIENT_ID` column, if present, is echoed back with each prediction so results "
        "can be matched to rows. Any other extra columns are ignored. Returns one "
        "prediction per row."
    ),
)
async def predict_csv(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse file as CSV: {exc}")

    missing = [gene for gene in feature_order if gene not in df.columns]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=(
                f"CSV is missing {len(missing)} required gene column(s), e.g. "
                f"{missing[:5]}. See GET /features for the full list."
            ),
        )

    id_column = next(
        (col for col in ["SAMPLE_ID", "PATIENT_ID"] if col in df.columns), None
    )

    X = df[feature_order]
    predicted_idx = model.predict(X)
    predicted_proba = model.predict_proba(X)

    predictions = []
    for i in range(len(df)):
        row = {
            "predicted_subtype": label_encoder.inverse_transform([predicted_idx[i]])[0],
            "probabilities": {
                class_name: float(prob)
                for class_name, prob in zip(label_encoder.classes_, predicted_proba[i])
            },
        }
        if id_column:
            row[id_column] = str(df.iloc[i][id_column])
        predictions.append(row)

    return {"model_name": model_name, "n_patients": len(df), "predictions": predictions}
