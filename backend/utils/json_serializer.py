import json
import numpy as np
import pandas as pd


def make_json_safe(obj):
    """
    Recursively convert numpy/pandas objects
    into JSON serializable Python objects.
    """

    if obj is None:
        return None

    # Python primitives
    if isinstance(obj, (str, int, float, bool)):
        return obj

    # NumPy
    if isinstance(obj, np.bool_):
        return bool(obj)

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        return float(obj)

    if isinstance(obj, np.ndarray):
        return obj.tolist()

    # Pandas
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")

    if isinstance(obj, pd.Series):
        return obj.tolist()

    # Dictionary
    if isinstance(obj, dict):
        return {
            str(k): make_json_safe(v)
            for k, v in obj.items()
        }

    # List / Tuple / Set
    if isinstance(obj, (list, tuple, set)):
        return [make_json_safe(v) for v in obj]

    # Fallback
    return str(obj)