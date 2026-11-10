# Model Card: Customer Segment Classifier (fintech wallet app)

## 1. Overview
A scikit-learn pipeline that predicts which **customer segment** (Low, Medium or High value) a wallet-app customer belongs to. The segments were discovered by K-Means clustering, then a classifier learns to assign new customers to them.

## 2. Dataset
- **3 synthetic (made-up) Excel tables** linked by `customer_id`: `customers` (age, gender, city, income), `accounts` (account type, balance, transactions, logins, churned), `support_tickets` (category, resolution hours, satisfaction).
- Stored in SQLite and combined with SQL JOINs into **1000 rows** (one per customer).
- Cleaning: missing income filled with the median; customers with no tickets get 0 tickets.
- Segment sizes: {'Low value': 466, 'Medium value': 343, 'High value': 191}.

## 3. Methodology
1. Scale 4 behaviour columns (balance, transactions, logins, ticket count) and run **K-Means** (k = 3, chosen with the elbow plot; silhouette 0.411). DBSCAN was also tested but left many customers as noise, so K-Means labels are used.
2. Use the K-Means cluster as the target. Inputs: age, income, balance, transactions, logins, ticket count, gender, city.
3. Pipeline: `StandardScaler` for numbers, `OneHotEncoder` for text, then the classifier.
4. Two algorithms (Logistic Regression, Random Forest) were tuned with `GridSearchCV` (5-fold, f1 macro). Winner: **Logistic Regression** with settings {'model__C': 1}.

## 4. Evaluation (20% hidden test set, 200 customers)
| Metric | Score |
|---|---|
| Accuracy | 1.000 |
| Precision (macro) | 1.000 |
| Recall (macro) | 1.000 |
| F1-score (macro) | 1.000 |

The confusion matrix is saved as `confusion_matrix.png`. The saved `.joblib` model was reloaded and gave identical predictions and probabilities to the original.

## 5. Intended use
- Learning and demonstration of an end-to-end ML pipeline.
- Example use: grouping customers into value segments to plan retention or marketing ideas.
- Inputs must pass the schema in `input_schema.json` (required features, types, allowed values).

## 6. Limitations
- The data is **synthetic**, so results do not describe real customers.
- The target labels come from K-Means on almost the same columns, so near-perfect scores are expected and do not prove real-world accuracy.
- Clusters are only a description of the current data. If customer behaviour changes, the clusters and the model must be rebuilt.
- Only 1000 customers, 5 cities and 2 genders; unseen cities or values are rejected by validation.

## 7. Potential risks
- **Unfair treatment:** gender and city are inputs. Using segments to decide prices, limits, credit or service levels could disadvantage groups of people.
- **Wrong labelling:** a low-value label could lead to a customer being ignored; treat it as a hint, not a judgement.
- **Privacy:** real customer data (income, balances) is sensitive and needs proper protection and consent.
- **Not for:** credit scoring, fraud decisions or any automated decision with legal or financial effect.
