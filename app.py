import json

import joblib
import pandas as pd
import streamlit as st

from validation import predict_segment, validate_input

st.set_page_config(page_title="Customer Segment Predictor", page_icon="💳", layout="wide")

# ---------- load the saved model and files made by the notebook ----------
@st.cache_resource
def load_model():
    return joblib.load("cluster_model.joblib")


@st.cache_data
def load_json(path):
    with open(path) as f:
        return json.load(f)


model = load_model()
schema = load_json("input_schema.json")
metrics = load_json("metrics.json")
features = schema["features"]

# ---------- what each segment means for the business ----------
SEGMENTS = {
    "Low value": {
        "color": "#E8590C",
        "light": "#FFF4E6",
        "meaning": "Small balance, few transactions and logins. This group has the highest chance of leaving the app.",
        "action": "Send re-engagement offers, simple onboarding tips and fast support follow-ups.",
    },
    "Medium value": {
        "color": "#1C7ED6",
        "light": "#E7F5FF",
        "meaning": "Regular users with a steady balance and activity. A stable, growing group.",
        "action": "Encourage more use with rewards, bill payments and savings features.",
    },
    "High value": {
        "color": "#2B8A3E",
        "light": "#EBFBEE",
        "meaning": "Large balance and very active. These customers rarely leave.",
        "action": "Protect the relationship: priority support and premium benefits.",
    },
}

PRESETS = {
    "Custom": {"age": 35, "gender": "Male", "city": "Karachi", "monthly_income": 100000, "avg_balance": 50000,
               "monthly_transactions": 15, "monthly_logins": 12, "ticket_count": 1},
    "Example: low-value user": {"age": 24, "gender": "Male", "city": "Karachi", "monthly_income": 50000, "avg_balance": 9000,
                                "monthly_transactions": 5, "monthly_logins": 3, "ticket_count": 2},
    "Example: medium-value user": {"age": 38, "gender": "Female", "city": "Islamabad", "monthly_income": 120000,
                                   "avg_balance": 80000, "monthly_transactions": 25, "monthly_logins": 20, "ticket_count": 1},
    "Example: high-value user": {"age": 45, "gender": "Male", "city": "Lahore", "monthly_income": 250000,
                                 "avg_balance": 300000, "monthly_transactions": 45, "monthly_logins": 30, "ticket_count": 0},
}

# ---------- a little styling ----------
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1200px;}
    .hero {background: linear-gradient(135deg, #1b2a49 0%, #2f4b7c 100%); padding: 1.6rem 2rem;
           border-radius: 16px; color: white; margin-bottom: 1.2rem;}
    .hero h1 {color: white; margin: 0; font-size: 2rem;}
    .hero p {color: #d0d9ec; margin: .4rem 0 0 0;}
    .result-card {border-radius: 16px; padding: 1.4rem 1.6rem; margin-bottom: 1rem; border-left: 8px solid;}
    .result-card .label {font-size: .85rem; letter-spacing: .08em; text-transform: uppercase; opacity: .75;}
    .result-card .name {font-size: 2.1rem; font-weight: 700; margin: .1rem 0 .5rem 0;}
    .result-card p {margin: .2rem 0;}
    </style>
    <div class="hero">
      <h1>💳 Customer Segment Predictor</h1>
      <p>Fintech wallet app · enter a customer and the model places them in a Low, Medium or High value group.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_one, tab_batch, tab_perf, tab_card = st.tabs(
    ["🔮 Single customer", "📄 Batch (CSV)", "📊 Model performance", "📝 Model card"]
)

# =====================================================================
# TAB 1: one customer
# =====================================================================
with tab_one:
    left, right = st.columns([1.1, 1], gap="large")

    with left:
        st.subheader("Customer details")
        preset_name = st.selectbox("Start from", list(PRESETS.keys()))
        p = PRESETS[preset_name]
        k = preset_name  # widget keys change with the preset, so the widgets reset to its values

        c1, c2 = st.columns(2)
        age = c1.slider("Age", 18, 80, p["age"], key=f"age_{k}")
        gender = c2.radio("Gender", features["gender"]["allowed"], index=features["gender"]["allowed"].index(p["gender"]),
                          horizontal=True, key=f"gender_{k}")
        city = st.selectbox("City", features["city"]["allowed"], index=features["city"]["allowed"].index(p["city"]),
                            key=f"city_{k}")

        c3, c4 = st.columns(2)
        income = c3.number_input("Monthly income (PKR)", 0, 1_000_000, p["monthly_income"], step=5000, key=f"inc_{k}")
        balance = c4.number_input("Average wallet balance (PKR)", 0, 2_000_000, p["avg_balance"], step=5000, key=f"bal_{k}")

        c5, c6, c7 = st.columns(3)
        transactions = c5.slider("Transactions / month", 0, 100, p["monthly_transactions"], key=f"tx_{k}")
        logins = c6.slider("App logins / month", 0, 60, p["monthly_logins"], key=f"lg_{k}")
        tickets = c7.slider("Support tickets", 0, 10, p["ticket_count"], key=f"tk_{k}")

    customer = {
        "age": int(age), "gender": gender, "city": city, "monthly_income": float(income),
        "avg_balance": float(balance), "monthly_transactions": int(transactions),
        "monthly_logins": int(logins), "ticket_count": int(tickets),
    }
    result = predict_segment(customer, model, schema)

    with right:
        st.subheader("Prediction")
        if not result["ok"]:
            st.error("The input did not pass validation:")
            for message in result["errors"]:
                st.write("•", message)
        else:
            info = SEGMENTS[result["segment"]]
            st.markdown(
                f"""
                <div class="result-card" style="background:{info['light']}; border-color:{info['color']}; color:#1a1a1a;">
                  <div class="label">Predicted segment</div>
                  <div class="name" style="color:{info['color']};">{result['segment']}</div>
                  <p><b>What it means:</b> {info['meaning']}</p>
                  <p><b>Suggested focus:</b> {info['action']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("**How sure is the model?**")
            for name, prob in sorted(result["probabilities"].items(), key=lambda x: -x[1]):
                st.progress(prob, text=f"{name}: {prob:.1%}")
            with st.expander("✅ Input validation passed: see what was checked"):
                st.write("All 8 required features are present, have the right type and are inside the allowed values.")
                st.json(customer)

# =====================================================================
# TAB 2: batch CSV (here validation really matters)
# =====================================================================
with tab_batch:
    st.subheader("Predict many customers from a CSV file")
    st.write("Upload a CSV with these columns: " + ", ".join(f"`{c}`" for c in features))
    with open("sample_batch.csv", "rb") as f:
        st.download_button("Download a sample CSV (last row is intentionally wrong)", f, "sample_batch.csv", "text/csv")

    uploaded = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded is not None:
        data = pd.read_csv(uploaded)
        st.write(f"Loaded **{len(data)}** rows.")

        good_rows, problems = [], []
        for i, row in enumerate(data.to_dict("records")):
            errors = validate_input(row, features)
            if errors:
                problems.append({"row": i + 2, "problems": "; ".join(errors)})   # +2 = header line + 1-based
            else:
                good_rows.append(i)

        if good_rows:
            valid = data.loc[good_rows, list(features.keys())].copy()
            valid["predicted_segment"] = [schema["segments"][str(c)] for c in model.predict(valid)]
            st.success(f"{len(valid)} rows passed validation and were predicted.")
            st.dataframe(valid, width="stretch")
            st.download_button("Download predictions", valid.to_csv(index=False).encode(), "predictions.csv", "text/csv")
            st.bar_chart(valid["predicted_segment"].value_counts())
        if problems:
            st.error(f"{len(problems)} rows were rejected by validation (not predicted):")
            st.dataframe(pd.DataFrame(problems), width="stretch", hide_index=True)

# =====================================================================
# TAB 3: model performance
# =====================================================================
with tab_perf:
    st.subheader("How good is the model?")
    st.caption(f"Best model: **{metrics['best_model']}**, tested on {metrics['test_rows']} customers it had never seen.")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Accuracy", f"{metrics['accuracy']:.1%}")
    m2.metric("Precision", f"{metrics['precision_macro']:.1%}")
    m3.metric("Recall", f"{metrics['recall_macro']:.1%}")
    m4.metric("F1-score", f"{metrics['f1_macro']:.1%}")

    a, b = st.columns(2, gap="large")
    with a:
        st.markdown("**Confusion matrix**")
        st.image("confusion_matrix.png")
    with b:
        st.markdown("**Segment sizes**")
        st.bar_chart(pd.Series(metrics["segment_sizes"]))
        st.markdown("**Hyperparameter tuning (cross-validation)**")
        st.dataframe(pd.DataFrame(metrics["tuning"]), width="stretch", hide_index=True)

    st.info(
        "Scores are close to 100% because the segments were created by K-Means from almost the same columns, "
        "so the classifier re-learns that rule. This is a demo on synthetic data, not a real-world accuracy claim."
    )

# =====================================================================
# TAB 4: model card
# =====================================================================
with tab_card:
    with open("MODEL_CARD.md", encoding="utf-8") as f:
        st.markdown(f.read())
