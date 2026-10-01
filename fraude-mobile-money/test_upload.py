import pandas as pd 
import requests
CSV_PATH = "data/paysim.csv"
SAMPLE_PATH = "data/paysim_sample.csv"
SAMPLE_SIZE = 1000
API_URL = "http://127.0.0.1:8000/api/upload/"
def build_sample():
    df = pd.read_csv(CSV_PATH)
    fraudes = df[df["isFraud"] == 1]
    normales = df[df["isFraud"] == 0]
    n_fraudes = min(50, len(fraudes))
    n_normales = SAMPLE_SIZE - n_fraudes
    sample = pd.concat([
        fraudes.sample(n=n_fraudes, random_state=42),
        normales.sample(n=n_normales, random_state=42),
    ]).sample(frac=1, random_state=42)
    sample.to_csv(SAMPLE_PATH, index=False)
    print(f"Echantillon cree: {len(sample)} lignes ({n_fraudes} fraudes reelles -> {SAMPLE_PATH})")

if __name__ == "__main__":
    build_sample()    