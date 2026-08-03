# TCGA-BRCA Molecular Subtype Classifier

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-006ACC?style=flat)
![SQL](https://img.shields.io/badge/SQL-4479A1?style=flat&logo=postgresql&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/status-in_progress-yellow?style=flat)
![License](https://img.shields.io/badge/license-MIT-blue?style=flat)

## The Problem

Breast cancer isn't one disease — molecular subtype (PAM50: Luminal A, Luminal B, HER2-enriched, Basal-like) drives treatment choice (hormonal therapy vs. anti-HER2 therapy vs. chemotherapy). Subtyping from gene expression is a real clinical decision-support task, not a synthetic benchmark.

**This project builds an end-to-end, production-shaped pipeline that predicts PAM50 molecular subtype from gene expression and clinical covariates — from raw public data through a deployed, queryable API.**

---

## Pipeline

1. **Data acquisition, QC & EDA** — clinical (PAM50 subtype) + gene expression data for TCGA-BRCA, pulled from cBioPortal's public API; PCA, gene correlation structure, and marker-gene checks by subtype.
2. **SQL layer** — processed data loaded into a relational database; cohort and feature-set queries run in SQL, then passed to pandas for modeling.
3. **Modeling** — Logistic Regression, Random Forest, and XGBoost compared via cross-validation (accuracy, F1, ROC-AUC).
4. **Interpretability** — SHAP values on the best model, cross-checked against known breast-cancer subtype biology (e.g. ESR1, ERBB2, MKI67).
5. **API** — FastAPI endpoint serving the trained model (patient features in → subtype prediction out).
6. **Deployment** — Dockerized and deployed to Render (free tier).

---

## Repository Structure

```
tcga-brca-subtype-classifier/
├── data/                     # Raw and processed data (clinical + expression)
├── notebooks/
│   ├── 01_data_acquisition_qc.ipynb
│   ├── 02_modeling_cross_validation.ipynb
│   └── 03_shap_interpretability.ipynb
├── api/                      # FastAPI app, trained model bundle, test script
├── figures/
├── requirements.txt
└── README.md
```

## Notebooks

| # | Notebook | Status | Description |
|---|---|---|---|
| 01 | `01_data_acquisition_qc.ipynb` | ✅ Complete | Pull PAM50 clinical annotations + expression data from cBioPortal; QC, EDA (PCA, gene correlation, marker genes) |
| 02 | `02_modeling_cross_validation.ipynb` | ✅ Complete | Load data into SQL, assemble cohort via SQL query, compare LogReg/Random Forest/XGBoost via cross-validation (XGBoost best: F1-macro 0.86, accuracy 91%), evaluate on held-out test set (93% accuracy), export model for the API |
| 03 | `03_shap_interpretability.ipynb` | ✅ Complete | SHAP-based model interpretation (TreeExplainer), global feature ranking, biological cross-validation against ESR1/ERBB2/MKI67, single-prediction explanation |

---

## Data Source

**cBioPortal for Cancer Genomics** (public API, no authentication required): [www.cbioportal.org](https://www.cbioportal.org) — study: TCGA, Breast Invasive Carcinoma (BRCA), PanCancer Atlas.

Underlying data originates from **The Cancer Genome Atlas (TCGA)**, a public resource of the National Cancer Institute and National Human Genome Research Institute.

---

## How to Run

```bash
git clone https://github.com/virginiagalvan/tcga-brca-subtype-classifier.git
cd tcga-brca-subtype-classifier
pip install -r requirements.txt
jupyter notebook notebooks/01_data_acquisition_qc.ipynb
```

API (once built):
```bash
cd api
uvicorn main:app --reload
```

---

## Author

**Virginia Galván, PhD** · Bioinformatics · Genomic & Multi-Omics Data Science
