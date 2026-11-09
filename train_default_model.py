import joblib
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "Crop_recommendation.csv"
MODEL_PATH = BASE_DIR / "models" / "tabpfn_crop_model.joblib"

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
TARGET = "label"

df = pd.read_csv(DATA_PATH)
X = df[FEATURES].apply(pd.to_numeric, errors="coerce")
y = df[TARGET].astype(str)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(f"Training RandomForestClassifier on {len(X_train)} samples across {y.nunique()} classes...")
model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

score = model.score(X_test, y_test)
print(f"Test accuracy: {score * 100:.2f}%")

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(model, MODEL_PATH)
print(f"Saved model to: {MODEL_PATH}")
