import os
import pickle
import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score
import random

MODEL_PATH = "ml_pipeline/online_model.pkl"
CLASSES = ["Healthy", "Drought", "Pest", "Nutrient Deficit"]

# In-memory store for evaluation on a synthetic validation set
# This ensures we have a held-out set to measure accuracy changes during /api/ml-feedback
VAL_X = []
VAL_y = []

def _generate_synthetic_data(num_samples=200):
    """
    Generates synthetic bootstrap data based on logical threshold ranges for the sensors.
    This provides our COLD START for the SGDClassifier.
    - Features: [nNDVI, lbp_texture_score, capacitance, acoustic_score]
    """
    X, y = [], []
    for _ in range(num_samples):
        # Base healthy
        healthy = random.random() > 0.6
        if healthy:
            X.append([random.uniform(0.65, 0.9), random.uniform(0, 0.2), random.uniform(0.7, 1.0), random.uniform(0, 0.15)])
            y.append("Healthy")
        else:
            issue = random.choice(["Drought", "Pest", "Nutrient Deficit"])
            if issue == "Drought":
                X.append([random.uniform(0.3, 0.5), random.uniform(0.1, 0.4), random.uniform(0.1, 0.4), random.uniform(0, 0.15)])
            elif issue == "Pest":
                X.append([random.uniform(0.4, 0.6), random.uniform(0.5, 0.9), random.uniform(0.5, 0.8), random.uniform(0.6, 1.0)])
            else: # Nutrient
                X.append([random.uniform(0.2, 0.5), random.uniform(0, 0.3), random.uniform(0.5, 0.8), random.uniform(0, 0.2)])
            y.append(issue)
    return np.array(X), np.array(y)

def initialize_model():
    """
    Bootstrap the model. 
    Trains incrementally on generated data, creating the cold-start weights.
    """
    global VAL_X, VAL_y
    clf = SGDClassifier(loss='log_loss', learning_rate='optimal', random_state=42) # log_loss effectively does incremental logistic regression
    
    boot_X, boot_y = _generate_synthetic_data(300)
    # Perform partial_fit with explicit class list
    clf.partial_fit(boot_X, boot_y, classes=CLASSES)
    
    # Generate our small held-out validation set to prove online learning improves accuracy
    VAL_X, VAL_y = _generate_synthetic_data(200)
    
    model_state = {
        "classifier": clf,
        "samples_seen": len(boot_y),
        "val_X": VAL_X.tolist(),
        "val_y": VAL_y.tolist() # Keep val split fixed so accuracy shifts are strictly from model updates
    }
    
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_state, f)
    
    return model_state

def load_model():
    if not os.path.exists(MODEL_PATH):
        return initialize_model()
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

def save_model(model_state):
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_state, f)

def get_status():
    state = load_model()
    clf = state["classifier"]
    X, y = np.array(state["val_X"]), np.array(state["val_y"])
    preds = clf.predict(X)
    acc = accuracy_score(y, preds)
    return {
        "samples_seen": state["samples_seen"],
        "validation_accuracy": round(acc, 4),
        "message": "Cold-started on synthetic threshold ranges. Held-out test set size: 200."
    }

def predict(features):
    """ features: list of [nNDVI, lbp, cap, acou] """
    state = load_model()
    clf = state["classifier"]
    X = np.array([features])
    pred = clf.predict(X)[0]
    probs = clf.predict_proba(X)[0]
    conf = max(probs)
    return pred, round(conf, 4)

def feedback(features, true_label):
    if true_label not in CLASSES:
        raise ValueError(f"Label must be one of {CLASSES}")
    state = load_model()
    clf = state["classifier"]
    X = np.array([features])
    y = np.array([true_label])
    
    # The actual online training update!
    clf.partial_fit(X, y)
    
    state["samples_seen"] += 1
    state["classifier"] = clf
    save_model(state)
    return get_status()

if __name__ == "__main__":
    # Ensure fresh restart if run directly
    if os.path.exists(MODEL_PATH):
        os.remove(MODEL_PATH)
    status = initialize_model()
    print("Model cleanly bootstrapped.")
    print("Initial Status:", get_status())
