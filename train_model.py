
import pandas as pd
import pickle

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    classification_report
)

# 1. Load dataset
data = pd.read_csv("heart.csv")

print("Dataset loaded successfully!")
print("Dataset shape:", data.shape)

# 2. Separate features and target
X = data.drop("target", axis=1)
y = data["target"]

# 3. Split dataset into training and testing data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("Training records:", len(X_train))
print("Testing records:", len(X_test))

# 4. Create and train Decision Tree model
model = DecisionTreeClassifier(
    random_state=42,
    max_depth=5
)

model.fit(X_train, y_train)

print("\nModel trained successfully!")

# 5. Evaluate model
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred) * 100

print("Accuracy:", round(accuracy, 2), "%")

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# 6. Save trained model
with open("heart_model.pkl", "wb") as file:
    pickle.dump(model, file)

print("\nModel saved successfully as heart_model.pkl!")
