import joblib
import os


MODEL_DIR = "models/"


def train_model(tenant_id, dataset):

    model = dataset.train_model()

    path = f"{MODEL_DIR}tenant_{tenant_id}_model.pkl"

    joblib.dump(model, path)

    return path


def load_model(tenant_id):

    path = f"{MODEL_DIR}tenant_{tenant_id}_model.pkl"

    return joblib.load(path)
    
    import joblib
import os
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

MODEL_DIR = "models/"


def train_model(tenant_id, data):

    X = data.drop("revenue", axis=1)
    y = data["revenue"]

    model = RandomForestRegressor()

    model.fit(X, y)

    path = f"{MODEL_DIR}/tenant_{tenant_id}_model.pkl"

    joblib.dump(model, path)

    return path


def load_model(tenant_id):

    path = f"{MODEL_DIR}/tenant_{tenant_id}_model.pkl"

    if os.path.exists(path):
        return joblib.load(path)

    return None


def self_learning_update(tenant_id, new_data):

    model = load_model(tenant_id)

    if model is None:
        return train_model(tenant_id, new_data)

    X = new_data.drop("revenue", axis=1)
    y = new_data["revenue"]

    model.fit(X, y)

    joblib.dump(model, f"{MODEL_DIR}/tenant_{tenant_id}_model.pkl")

    return model