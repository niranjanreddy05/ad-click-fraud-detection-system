import joblib

model = joblib.load("training/best_ml_model.pkl")

# Remove deprecated param if present
if hasattr(model, "use_label_encoder"):
    print("Removing deprecated use_label_encoder")
    del model.use_label_encoder

# Also clean params dict if present
if hasattr(model, "get_params"):
    params = model.get_params()
    if "use_label_encoder" in params:
        params.pop("use_label_encoder", None)
        model.set_params(**params)

joblib.dump(model, "training/best_ml_model_fixed.pkl")
print("Fixed model saved as best_ml_model_fixed.pkl")
