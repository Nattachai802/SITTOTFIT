import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, accuracy_score
import joblib

df = pd.read_csv('camera/utils/Dataset_spine.csv')

# ------- 1. Data Preprocessing -------
df["label"] = (df["Class_att"]
               .str.strip()
               .str.lower()
               .eq("abnormal")
              ).astype(int) # Convert to binary label


# ------- 1.1 Data mapping -------
df_feat = pd.DataFrame({
    # hip_angle  ≈ pelvic_tilt
    "hip_angle": df["pelvic_tilt"],

    # back_angle ≈ avg(lumbar_lordosis_angle, sacral_slope)
    "back_angle": (df["lumbar_lordosis_angle"] + df["sacral_slope"]) / 2,

    # neck_angle ≈ cervical_tilt
    "neck_angle": df["cervical_tilt"],

    # shoulder_angle ≈ thoracic_slope (proxy)
    "shoulder_angle": df["thoracic_slope"],

    # head_tilt_angle ≈ direct_tilt
    "head_tilt_angle": df["direct_tilt"],

    # knee_angle ไม่มีใน X-ray → สร้าง dummy 110° ± 3°
    "knee_angle": 110 + np.random.normal(0, 3, size=len(df)),

    # label (0 = Normal, 1 = Abnormal)
    "label": df["label"]
})

# ------- 1.2 5-fold cross validation -------
X = df_feat.drop(columns=["label"])
y = df_feat["label"].values

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

best_auc, best_model = 0.0, None
fold_results = []

for fold, (tr_idx, val_idx) in enumerate(skf.split(X, y), 1):
    X_train, y_train = X.iloc[tr_idx], y[tr_idx]
    X_val,   y_val   = X.iloc[val_idx], y[val_idx]

    train_ds = lgb.Dataset(X_train, label=y_train)
    val_ds   = lgb.Dataset(X_val,   label=y_val)

    params = {
        "objective": "binary",
        "metric": "auc",
        "boosting_type": "gbdt",
        "num_leaves": 31,
        "learning_rate": 0.05,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "seed": 42,
        "verbosity": -1,
    }

    model = lgb.train(
        params,
        train_ds,
        num_boost_round=800,
        valid_sets=[val_ds],
        callbacks=[lgb.early_stopping(50)]
    )

    # ---------- 3. ประเมิน ----------
    y_pred_prob = model.predict(X_val, num_iteration=model.best_iteration)
    auc  = roc_auc_score(y_val, y_pred_prob)
    acc  = accuracy_score(y_val, (y_pred_prob >= 0.5).astype(int))
    fold_results.append({"fold": fold, "AUC": auc, "ACC": acc})
    print(f"Fold {fold}: AUC={auc:.3f}  ACC={acc:.3f}  trees={model.best_iteration}")

    # เก็บโมเดลที่ AUC สูงสุด
    if auc > best_auc:
        best_auc, best_model = auc, model

# ---------- 4. สรุปผล ----------
print("\n=== CV Summary ===")
for r in fold_results:
    print(f"Fold {r['fold']}:  AUC={r['AUC']:.3f}  ACC={r['ACC']:.3f}")
print(f"Best AUC = {best_auc:.3f}")

# ---------- 5. บันทึกโมเดล ----------
best_model.save_model("spine_risk_lgbm.txt")
joblib.dump(best_model, "spine_risk_lgbm.pkl")
print("✅  Saved best model to spine_risk_lgbm.txt / pkl")

# ---------- 6. Runtime Prediction Function ----------
bst = joblib.load("spine_risk_lgbm.pkl")   # โหลดครั้งเดียวตอนเริ่มเซิร์ฟเวอร์

