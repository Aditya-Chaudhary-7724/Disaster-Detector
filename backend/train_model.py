import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

DATA_PATH = os.path.join("datasets", "disaster_dataset.csv")
MODEL_PATH = os.path.join("models", "disaster_model.pkl")

def main():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    # Inputs
    X = df.drop(columns=["risk_label"])
    y = df["risk_label"]

    # categorical + numeric split
    categorical_cols = ["disaster", "soil_moisture"]  # soil_moisture we treat numeric but keep for simplicity later
    numeric_cols = [c for c in X.columns if c not in categorical_cols]

    # Fix soil_moisture as numeric (remove from categorical)
    if "soil_moisture" in categorical_cols:
        categorical_cols.remove("soil_moisture")
        numeric_cols.append("soil_moisture")

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
            ("num", "passthrough", numeric_cols),
        ]
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        random_state=42
    )

    clf = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42
    )

    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)

    os.makedirs("models", exist_ok=True)
    joblib.dump(clf, MODEL_PATH)

    print("✅ Model trained successfully!")
    print(f"✅ Saved model -> {MODEL_PATH}")
    print(f"✅ Accuracy (demo dataset): {acc:.2f}")

if __name__ == "__main__":
    main()
