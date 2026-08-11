from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, ListFlowable, ListItem
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib import colors

output_path = Path(__file__).with_name('ai_training_tutorial.pdf')

content = []
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleStyle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=colors.HexColor('#0B3D91'), alignment=TA_LEFT, spaceAfter=12))
styles.add(ParagraphStyle(name='HeadingStyle', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=colors.HexColor('#0B3D91'), spaceBefore=10, spaceAfter=6))
styles.add(ParagraphStyle(name='BodyStyle', parent=styles['BodyText'], fontName='Helvetica', fontSize=10.5, leading=14, alignment=TA_JUSTIFY, spaceAfter=6))
styles.add(ParagraphStyle(name='BulletStyle', parent=styles['BodyText'], fontName='Helvetica', fontSize=10.5, leading=14, alignment=TA_LEFT, leftIndent=14, bulletIndent=0, spaceAfter=4))
styles.add(ParagraphStyle(name='CodeStyle', parent=styles['Code'], fontName='Courier', fontSize=8.5, leading=11.5, textColor=colors.HexColor('#222222'), backColor=colors.HexColor('#F4F6F8'), borderPadding=6, spaceAfter=8))
styles.add(ParagraphStyle(name='SmallStyle', parent=styles['BodyText'], fontName='Helvetica-Oblique', fontSize=9, leading=12, textColor=colors.HexColor('#555555'), spaceAfter=6))

content.append(Paragraph('AI Model Training Tutorial', styles['TitleStyle']))
content.append(Paragraph('A complete beginner-to-professional guide', styles['SmallStyle']))
content.append(Spacer(1, 10))

sections = [
    ('1. What is an AI model?', 'An AI model is a mathematical system that learns patterns from data and uses those patterns to make predictions. In an AML system, it can help decide whether a transaction looks normal, suspicious, or high risk.'),
    ('2. The simplest idea behind training', 'Training means showing the model many examples and letting it learn from them. Over time, it becomes better at predicting answers for new cases.'),
    ('3. Core words you must know', 'Important concepts include data, features, labels, model, training, and prediction. Features are the inputs; labels are the correct answers.'),
    ('4. The full training workflow', 'A typical workflow is: collect data, clean it, choose features, label examples, split into train/test sets, choose an algorithm, train the model, evaluate it, and save it.'),
    ('5. Step-by-step training with a simple example', 'A tiny dataset can be created with transaction examples, and each example can include a label such as safe or suspicious.'),
    ('6. AI models in depth', 'Different models exist such as linear regression, logistic regression, decision trees, random forests, SVMs, neural networks, and gradient boosting. Each has strengths and weaknesses.'),
    ('7. What happens during training?', 'The model makes predictions, compares them with the correct answers, measures error, and adjusts its internal parameters to improve.'),
    ('8. Loss functions', 'Loss functions tell us how wrong the model is. The goal is to reduce that loss over time.'),
    ('9. Gradient descent', 'Gradient descent is the process of nudging the model parameters in the direction that reduces error.'),
    ('10. Overfitting and underfitting', 'Underfitting means the model is too simple; overfitting means it memorizes the training data and performs poorly on new data.'),
    ('11. Training a real model', 'In practice, we use a structured workflow: split data, preprocess, train, evaluate, and tune hyperparameters.'),
    ('12. How this applies to AML', 'AML systems use transaction features such as amount, frequency, account behavior, and recipient patterns to detect suspicious activity.'),
    ('13. Why AML models are tricky', 'AML modeling is difficult because fraud patterns change constantly and both false positives and false negatives are costly.'),
    ('14. What happens after training?', 'After training, the model is saved and used to make predictions on new incoming transactions.'),
    ('15. Final takeaway', 'Training an AI model is a disciplined sequence of learning from examples, checking results, and refining the model until it performs well.')
]

for title, body in sections:
    content.append(Paragraph(title, styles['HeadingStyle']))
    content.append(Paragraph(body, styles['BodyStyle']))
    content.append(Spacer(1, 4))

content.append(Paragraph('Code Example: Simple Python Dataset', styles['HeadingStyle']))
code1 = '''import pandas as pd

data = pd.DataFrame([
    {"amount": 100, "is_new_recipient": 0, "type": "transfer", "label": "safe"},
    {"amount": 2500, "is_new_recipient": 1, "type": "transfer", "label": "suspicious"},
    {"amount": 800, "is_new_recipient": 0, "type": "deposit", "label": "safe"},
    {"amount": 15000, "is_new_recipient": 1, "type": "transfer", "label": "suspicious"},
])

print(data)
'''
content.append(Paragraph(code1, styles['CodeStyle']))

content.append(Paragraph('Code Example: Logistic Regression', styles['HeadingStyle']))
code2 = '''from sklearn.linear_model import LogisticRegression

X = [[100], [500], [1000], [5000], [10000]]
y = [0, 0, 0, 1, 1]

model = LogisticRegression()
model.fit(X, y)

print(model.predict([[3000]]))
print(model.predict_proba([[3000]]))
'''
content.append(Paragraph(code2, styles['CodeStyle']))

content.append(Paragraph('Code Example: Random Forest', styles['HeadingStyle']))
code3 = '''from sklearn.ensemble import RandomForestClassifier

X = [[100, 0], [6000, 1], [200, 0], [8000, 1]]
y = [0, 1, 0, 1]

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

print(model.predict([[4500, 1]]))
'''
content.append(Paragraph(code3, styles['CodeStyle']))

content.append(Paragraph('Code Example: End-to-End Training Workflow', styles['HeadingStyle']))
code4 = '''import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

data = pd.DataFrame([
    {"amount": 100, "is_new_recipient": 0, "transaction_type": "deposit", "label": "safe"},
    {"amount": 2500, "is_new_recipient": 1, "transaction_type": "transfer", "label": "suspicious"},
    {"amount": 800, "is_new_recipient": 0, "transaction_type": "withdrawal", "label": "safe"},
    {"amount": 15000, "is_new_recipient": 1, "transaction_type": "transfer", "label": "suspicious"},
])

X = data[["amount", "is_new_recipient", "transaction_type"]]
y = data["label"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

numeric_features = ["amount", "is_new_recipient"]
categorical_features = ["transaction_type"]

numeric_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore"))
])

preprocess = ColumnTransformer([
    ("num", numeric_transformer, numeric_features),
    ("cat", categorical_transformer, categorical_features)
])

model = Pipeline([
    ("preprocess", preprocess),
    ("classifier", LogisticRegression())
])

model.fit(X_train, y_train)
predictions = model.predict(X_test)

print(classification_report(y_test, predictions))
'''
content.append(Paragraph(code4, styles['CodeStyle']))

content.append(Paragraph('Final Note', styles['HeadingStyle']))
content.append(Paragraph('This tutorial is meant to build intuition first and then connect that intuition to practical machine learning workflows. The goal is not just to memorize code, but to understand the logic behind how AI learns.', styles['BodyStyle']))

pdf = SimpleDocTemplate(str(output_path), pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
pdf.build(content)
print(output_path)
