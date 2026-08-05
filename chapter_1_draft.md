# CHAPTER 1: INTRODUCTION

**Project title:** *Design and Implementation of a Machine Learning-Based Real-Time Anti-Money Laundering Monitoring System for Simulated Banking Transactions in Zimbabwe*

## 1.1 Introduction

This chapter introduced the project and the setting in which it was undertaken. The project concerned the design and implementation of a prototype that monitored simulated banking transactions, assigned risk scores, and presented alerts to authorised users through a web-based compliance dashboard. The chapter described the background to anti-money-laundering (AML) monitoring, the problem addressed by the project, its aim and objectives, and the boundaries within which the prototype was developed. It also presented the development instruments, work plan and rationale for the work.

## 1.2 Background of the Study

Money laundering involves making funds obtained through unlawful activity appear to have come from a legitimate source. Financial institutions are expected to understand their customers, monitor transactions and investigate activity that appears inconsistent with a customer's known profile. This responsibility becomes more difficult where transactions are frequent, values differ widely and activity can occur across several accounts in a short period.

AML transaction monitoring has traditionally relied heavily on predefined rules. A rule may, for example, identify a transaction above a threshold or a sequence of transfers within a specified period. Rules remain useful because they are understandable and can be linked to institutional policy. Their weakness is that they do not readily adapt when behaviour changes, and a single pattern may be legitimate for one customer but unusual for another. Jensen and Iosifidis [3] distinguish between customer risk profiling and suspicious-behaviour flagging, and identify the availability of suitable data, interpretability and fairness as continuing concerns for machine-learning work in AML.

Machine learning can complement, rather than replace, rule-based monitoring. It can analyse several transaction characteristics together, including amount, transaction type, timing, frequency and deviations from a customer's previous activity. The Financial Action Task Force (FATF) reported that responsible use of technology can make AML/CFT measures faster and more effective, while also warning that transparency, privacy, cybersecurity and accountable human oversight must be considered [2]. For that reason, a risk score or model prediction should be treated as an alert for a compliance officer to review, not as proof that a customer has committed an offence.

Zimbabwe remained in enhanced follow-up after the 2024 FATF follow-up assessment, even though progress had been made on some technical-compliance matters [1]. This context made a locally relevant teaching and prototyping platform useful. The proposed system was not intended to represent the Financial Intelligence Unit (FIU), replace a bank's regulatory AML programme, or submit reports to an authority. Instead, it demonstrated a controlled workflow from transaction creation to risk assessment, alert generation, case review and a draft suspicious-activity-report record.

Access to real bank transaction data is restricted by confidentiality, privacy and security requirements. It is also a well-recognised research obstacle: Altman *et al.* [4] noted that real data for training AML models is generally unavailable and that synthetic data supports controlled evaluation because the expected labels are known. The project therefore used simulated, labelled transactions. The simulation included ordinary activity and selected scenarios associated with elevated risk, such as unusual transaction values, rapid transfers and repeated activity. This choice made it possible to test the application without exposing personal or banking data.

The project addressed a practical gap between a static demonstration of AML rules and an operational prototype that combined transaction simulation, hybrid risk assessment, live alerts, role-based access and case handling. The application used rules and model-assisted anomaly indicators together so that a user could see why a transaction had been flagged and could document a review decision.

## 1.3 Problem Definition

Monitoring a large stream of banking transactions using only fixed rules is difficult because the same value or transaction type can have different meanings for different customers. Fixed thresholds may generate alerts that are not useful, while evolving or multi-step patterns may not be recognised promptly. At the same time, real transaction data cannot be freely used for developing or demonstrating a student system. There was therefore a need for a safe prototype that could simulate banking activity, assess transactions as they were processed, combine rule-based and machine-learning indicators, and provide authorised compliance users with understandable alerts and case-review tools. The system had to support human review rather than make automatic accusations or regulatory submissions.

## 1.4 Aim

To design and implement a machine-learning-based real-time AML monitoring prototype that analysed simulated banking transactions, produced explainable risk alerts and supported compliance review within a Zimbabwean banking context.

## 1.5 Objectives

The project objectives were:

1. To simulate labelled banking transactions representing normal and selected higher-risk behavioural scenarios for controlled system testing.
2. To process incoming transactions in real time and derive transaction and behavioural features for risk assessment.
3. To combine rule-based indicators with machine-learning and anomaly-detection outputs to calculate a transaction risk score.
4. To generate and prioritise explainable alerts for transactions whose risk scores met the defined threshold.
5. To implement role-based compliance case handling for reviewing, escalating and resolving alerts.

## 1.6 Limitations

The prototype was evaluated using simulated data. Although the scenarios were designed to be plausible, they could not reproduce the full complexity, volume or quality of a live institution's transaction history. Consequently, any measured model performance should not be interpreted as performance at a commercial bank.

The model could produce false positive and false negative alerts. A high score indicated that a transaction required review; it did not establish criminal conduct. The output therefore depended on a compliance user recording an informed decision.

The application was developed and tested on a single development machine. Its response under production-scale traffic, multiple institutions or distributed data sources was outside the evaluation scope. Features such as external watchlist feeds, production message brokers and automated reporting to regulators were represented only where they assisted the prototype workflow.

Finally, the project time frame limited dataset refinement, model comparison and user evaluation. The work concentrated on a demonstrable and testable prototype rather than a production deployment.

## 1.7 Delimitations

The project was limited to simulated account-based banking transactions. It focused on transaction monitoring, risk scoring, alerts and compliance-case handling. It did not investigate every predicate offence, conduct customer due diligence, verify identity documents or perform a full institutional AML/CFT risk assessment.

The system modelled selected suspicious patterns, including unusual amounts, rapid movement of funds and repeated transactions. It did not claim to detect every laundering method or to provide a national view of cross-border financial activity. The prototype did not connect to FIU, Reserve Bank of Zimbabwe, sanctions-list or external banking systems, and it did not file reports automatically. These decisions preserved the project as an educational, controlled demonstration and kept its handling of data within a reasonable scope.

## 1.8 Development Instruments

Table 1.1 presents the principal instruments used during development.

| Category | Instrument | Purpose |
|---|---|---|
| Hardware | Laptop with Intel Core i5 processor, 16 GB RAM and 512 GB SSD | Development, local model training and testing |
| Operating system | Windows 11 | Development environment |
| Programming language | Python 3 | Application logic, data processing and ML integration |
| Web framework | Flask and Flask-SocketIO | Web application, user sessions and live dashboard updates |
| Data and ML libraries | pandas, NumPy, scikit-learn, XGBoost, LightGBM, imbalanced-learn and joblib | Data preparation, model training, anomaly detection and model persistence |
| Database | SQLite for local testing; MySQL-compatible configuration for deployment | Storage of users, transactions, alerts, cases and audit records |
| Front-end | HTML, CSS, Bootstrap and JavaScript | Responsive dashboards and user interaction |
| Development and test tools | Visual Studio Code, Firefox and pytest | Coding, browser testing and automated tests |

## 1.9 Work Plan

The work was planned over 25 weeks. The schedule in Table 1.2 should be converted to a Gantt chart in the final Word document, with the caption placed above the table in accordance with the faculty guide.

Table 1.2: Project Work Plan

| Activity | 1–3 | 4–6 | 7–9 | 10–12 | 13–15 | 16–18 | 19–21 | 22–25 |
|---|---|---|---|---|---|---|---|---|
| Proposal refinement and Chapter 1 | ■ |  |  |  |  |  |  |  |
| Literature review | ■ | ■ |  |  |  |  |  |  |
| Requirements and system design |  | ■ | ■ |  |  |  |  |  |
| Dataset simulation and preprocessing |  |  | ■ | ■ |  |  |  |  |
| ML and risk-scoring development |  |  |  | ■ | ■ |  |  |  |
| Web application and dashboard development |  |  |  | ■ | ■ | ■ |  |  |
| Integration and testing |  |  |  |  |  | ■ | ■ |  |
| Evaluation, documentation and presentation preparation |  |  |  |  |  |  | ■ | ■ |

## 1.10 Justification / Rationale

The project was justified on practical, educational and technical grounds. First, it provided a safe way to demonstrate the stages of AML transaction monitoring without requiring access to confidential customer records. The simulated data approach allowed the test scenarios and their expected labels to be controlled, which was important for evaluating whether alerts and risk scores were being produced as intended [4].

Second, the system combined ideas that are often considered separately: transaction rules, anomaly detection, model-assisted scoring, explanation of risk factors, and the human case-review process. This allowed a compliance user to move beyond a list of alerts and see the transaction evidence, record notes and choose an appropriate status. The approach reflected the FATF position that technology should be used responsibly and with adequate oversight, not as an opaque substitute for professional judgement [2].

Third, the project produced a reusable learning artefact for students and prospective financial-technology practitioners. It illustrated how data engineering, machine learning, information security and web development can be combined in a financial-crime context. The resulting prototype could support later work on larger synthetic datasets, additional behavioural features, explainability testing, model fairness and controlled integration with approved data sources.

## 1.11 Summary

This chapter introduced the project to design and implement a machine-learning-based AML monitoring prototype for simulated banking transactions. It explained the limits of relying solely on static rules and established why model-assisted analysis should still retain human review and explainable evidence. The aim, objectives, limitations, delimitations, development instruments and work plan were presented. Chapter 2 will review AML monitoring approaches, machine-learning techniques and the research gap addressed by the proposed work.

## References

[1] Financial Action Task Force, “Zimbabwe’s progress in strengthening measures to tackle money laundering and terrorist financing,” Apr. 2024. [Online]. Available: https://www.fatf-gafi.org/en/publications/Mutualevaluations/fur-zimbabwe-2024.html. [Accessed: Aug. 4, 2026].

[2] Financial Action Task Force, *Opportunities and Challenges of New Technologies for AML/CFT*. Paris, France: FATF/OECD, 2021. [Online]. Available: https://www.fatf-gafi.org/content/dam/fatf-gafi/guidance/Opportunities-Challenges-of-New-Technologies-for-AML-CFT.pdf.

[3] R. I. T. Jensen and A. Iosifidis, “Fighting money laundering with statistics and machine learning,” *IEEE Access*, vol. 11, pp. 8889–8903, 2023, doi: 10.1109/ACCESS.2023.3239549.

[4] E. Altman, J. Blanuša, L. von Niederhäusern, B. Egressy, A. Anghel and K. Atasu, “Realistic synthetic financial transactions for anti-money laundering models,” *arXiv preprint* arXiv:2306.16424, 2023, doi: 10.48550/arXiv.2306.16424.
