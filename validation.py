import pandas as pd


def validate_input(customer, features):
    """Check one customer (a dict) against the input schema. Returns a list of error messages."""
    errors = []

    # 1) required features must be there, and no unknown extras
    for name in features:
        if name not in customer:
            errors.append(f"Missing required feature: {name}")
    for name in customer:
        if name not in features:
            errors.append(f"Unexpected feature: {name}")

    # 2) check type and allowed values of each feature we have
    for name, rule in features.items():
        if name not in customer:
            continue
        value = customer[name]

        # empty values (None or NaN) are not allowed
        if value is None or value != value:
            errors.append(f"{name}: value is empty")
            continue

        if rule["type"] == "category":
            if value not in rule["allowed"]:
                errors.append(f"{name}: '{value}' is not allowed. Choose from {rule['allowed']}")
        else:
            is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
            if not is_number:
                errors.append(f"{name}: must be a number, got '{value}'")
                continue
            if rule["type"] == "int" and float(value) != int(value):
                errors.append(f"{name}: must be a whole number, got {value}")
                continue
            if value < rule["min"] or value > rule["max"]:
                errors.append(f"{name}: {value} is outside the allowed range {rule['min']} to {rule['max']}")

    return errors


def predict_segment(customer, model, schema):
    """Validate first. If the input is fine, predict the customer segment."""
    errors = validate_input(customer, schema["features"])
    if errors:
        return {"ok": False, "errors": errors}

    # same columns, same order as in training
    row = pd.DataFrame([customer])[list(schema["features"].keys())]
    cluster = int(model.predict(row)[0])
    probabilities = model.predict_proba(row)[0]

    names = [schema["segments"][str(c)] for c in model.classes_]
    return {
        "ok": True,
        "cluster": cluster,
        "segment": schema["segments"][str(cluster)],
        "probabilities": dict(zip(names, [round(float(p), 3) for p in probabilities])),
    }
