# CHAPTER 2: LITERATURE REVIEW

## 2.1 Introduction

This chapter reviewed literature relevant to the proposed AI-based real-time anti-money-laundering (AML) detection system for simulated banking transactions. It defined the principal concepts, reviewed international, regional and Zimbabwean work, identified the gaps in existing approaches and described the proposed work. The review used a funnel approach, beginning with general AML monitoring approaches and narrowing to the Zimbabwean context.

### 2.1.1 Anti-Money-Laundering Transaction Monitoring

Money laundering was the process by which proceeds of crime were concealed or made to appear legitimate. It was commonly associated with placement of funds into the financial system, layering through movements intended to obscure the trail, and integration into apparently lawful assets. These stages did not always occur separately; therefore, one transaction alone might not expose the entire activity.

AML transaction monitoring was the ongoing examination of financial activity to identify transactions or patterns requiring further review. It formed part of the wider AML/CFT programme, which also included customer due diligence, record keeping, internal controls and suspicious-transaction reporting. FATF promoted a risk-based approach: institutions were expected to apply controls proportionate to the risks they faced [1]. An alert therefore indicated activity to be investigated; it was not proof of criminal conduct.

Risk-based monitoring considered indicators such as amount, frequency, time, transaction channel, beneficiary, rapid movement of funds and deviation from historical customer behaviour. These indicators could be combined to produce a low-, medium- or high-risk score. This was relevant to the present project, which was designed to score simulated transactions and make the reasons for high-risk alerts available to a compliance user.

### 2.1.2 Machine Learning, Anomaly Detection and Explainability

Machine learning enabled a system to learn patterns from data and use them to classify or score new records. Supervised learning used labelled suspicious and non-suspicious examples. Unsupervised learning, including anomaly detection, identified observations that differed materially from common behaviour without needing complete labels. A hybrid method combined rules, supervised outputs and anomaly indicators.

Jensen and Iosifidis [2] noted that AML modelling involved both customer risk profiling and suspicious-behaviour detection. They identified scarce labelled data, class imbalance, changing criminal behaviour, interpretability and fairness as major difficulties. Since genuinely suspicious transactions were rare, an apparently accurate model could still miss most important cases. For this reason, measures such as precision, recall, F1-score and false-positive rate were more informative than accuracy alone.

An anomaly detector could flag an unusually large, frequent or rapid transaction pattern, but unusual activity was not necessarily unlawful. FATF reported that new technologies could improve AML/CFT efficiency, while introducing risks involving data quality, privacy, cyber security, bias and transparency [3]. The literature therefore supported human oversight and explainable alerts. The proposed system retained a compliance reviewer and displayed the indicators that contributed to a risk score instead of treating a model output as an automatic accusation.

## 2.2 Analysis of Related Work

### 2.2.1 International Approaches

Traditional AML systems relied mainly on predefined rules. Examples included transactions above a threshold, repeated payments just below a threshold, rapid transfers, or unusually frequent activity. Rules were valuable because they were transparent and could be linked to institutional policy. However, they were static: a threshold suitable for one customer could be normal for another, and criminals could change behaviour to avoid known rules. Rule-only systems could therefore produce many false-positive alerts while missing subtle changes in behaviour or multi-step layering patterns.

Machine-learning approaches attempted to identify more complex relationships among transaction features. Classifiers such as random forests and gradient-boosting models could combine amount, time, transaction type and behavioural features to estimate risk. Their limitation was that they depended on reliable historical labels, which were often incomplete because undetected laundering was not labelled. Models trained only on prior cases could also become less effective when typologies changed.

Graph-based approaches considered the relationships among accounts and transfers. Weber *et al.* [4] demonstrated graph convolutional networks for illicit-transaction detection in cryptocurrency data. Their work showed that relationships between entities could assist detection of networks and chains of transfers. However, graph methods required reliable relationship data, specialist skills and greater computing resources. They were less suitable as the only approach for a controlled undergraduate prototype.

The reviewed literature suggested that a hybrid approach was appropriate. Known red flags could be captured by rules; labelled patterns could be assessed by a machine-learning model; and unusual behaviour could be highlighted by anomaly detection. Combining these signals could improve prioritisation and provide clearer evidence for review than a single technique.

### 2.2.2 Synthetic Transactions and Simulation

Real banking data was difficult for researchers to obtain because it contained confidential, commercially sensitive and personally identifiable information. In addition, confirmed labels were incomplete because some laundering activity was never detected. These issues limited the reproducibility and fair evaluation of AML models.

Altman *et al.* [5] developed an agent-based generator for realistic synthetic financial transactions and AML scenarios. They argued that synthetic data enabled controlled evaluation because ground-truth labels were known and models could be compared using repeatable datasets. The IBM AMLSim project similarly provided a simulated banking environment for creating transactions and known suspicious patterns [6]. Simulation allowed researchers to create scenarios such as structuring, rapid movement of funds and abnormal account activity without exposing customer data.

Synthetic data nevertheless could not reproduce every characteristic of a live financial institution. It could contain simplified customer behaviour and known typologies, whereas real criminal strategies evolved. A result obtained from simulation should therefore not be interpreted as production-bank performance. The present project used simulation as an ethical and controlled method for testing a prototype, not as a substitute for authorised validation on live institutional data.

### 2.2.3 Real-Time Monitoring, Risk Scoring and Case Handling

Real-time monitoring assessed a transaction as it arrived, or shortly after it was received, rather than waiting for a long batch process. A practical architecture required transaction input, feature extraction, rule and model scoring, alert storage, dashboard updates and an audit trail. Low delay alone was insufficient: the risk decision also had to be reliable and understandable.

Risk scoring combined several indicators into one value or category to help analysts prioritise work. It could combine a rule score, an anomaly score and a model probability. However, a score without reasons could make an alert difficult to investigate. FATF's technology guidance supported transparent, secure and governed use of technology [3]. A useful alert should therefore show the relevant transaction details, triggered rules, risk factors and review history.

Many technical studies focused on classifier performance and did not demonstrate what happened after an alert was created. Case management was important because an authorised user needed to review evidence, add notes, escalate a concern or resolve a false positive. The proposed project addressed this operational gap by including a role-based dashboard that supported alert review and documented outcomes. It did not replace a bank's compliance programme or submit reports automatically to the FIU.

### 2.2.4 Regional African Context

African financial systems had experienced increasing digital payments, mobile money and cross-border transfers. These channels improved access and convenience but also increased the volume and speed of activity that institutions had to monitor. Cash-intensive activity, incomplete customer information, limited labelled data and constrained technical resources could make imported monitoring systems unsuitable without local calibration.

FATF recognised that digital transformation could improve AML/CFT effectiveness, provided that institutions addressed data protection, technical skills and governance [3]. In this context, an affordable, explainable and modular system using standard development tools was appropriate for learning and controlled experimentation. It could not substitute for the secure infrastructure, data sharing and regulatory coordination required in an operational financial institution.

### 2.2.5 Zimbabwean Context

Zimbabwe's Financial Intelligence Unit (FIU) issued AML/CFT guidelines as legally binding minimum standards for relevant sectors under the Money Laundering and Proceeds of Crime Act [7]. The National Money Laundering Risk Assessment highlighted effective transaction-monitoring systems and management commitment as significant to risk mitigation in the banking sector [8]. Zimbabwe's National Anti-Money Laundering Strategy also encouraged financial institutions and other reporting entities to adopt transaction-monitoring tools and modern technologies, including artificial intelligence where appropriate [9].

These documents established the local relevance of technology-supported monitoring. However, publicly available local material did not provide an openly accessible end-to-end prototype combining transaction simulation, real-time hybrid scoring, explainable alerts and role-based case handling for a Zimbabwean banking-learning context. Commercial systems were proprietary, while actual bank data could not be released for student experimentation. The local gap was therefore a safe demonstrator of the workflow from simulated transaction through risk assessment to accountable compliance review.

## 2.3 Gaps Identified

Table 2.1 presents the gaps identified from the reviewed literature.

Table 2.1: Gaps Identified from Related Work

| Identified gap | Evidence | Proposed response |
|---|---|---|
| Static rules could miss changing or multi-step behaviour and create false positives. | Rules were transparent but limited; ML added pattern-recognition capability [2]. | Combine rules, ML outputs and anomaly indicators. |
| Real AML data and complete labels were difficult to access. | Synthetic datasets enabled controlled, repeatable tests [5], [6]. | Generate labelled normal and higher-risk simulated transactions. |
| Model scores alone were insufficient for accountable decisions. | FATF emphasised transparency and human oversight [3]. | Show risk factors and require authorised review. |
| Many studies did not include analyst workflow after detection. | Detection research often concentrated on model results [2], [4]. | Provide a dashboard for notes, escalation, resolution and audit history. |
| An integrated, locally relevant learning prototype was not readily available. | Zimbabwean policy supported stronger monitoring and modern technology [8], [9]. | Build a Zimbabwe-focused controlled prototype without confidential data or regulatory integrations. |

## 2.4 Proposed Work

The proposed work was an AI-based real-time AML detection prototype for simulated banking transactions. A simulation module generated normal transactions and selected higher-risk scenarios, including structuring, unusual transaction values, rapid movement of funds and repeated activity. As each transaction was processed, the system derived relevant features and assessed them using predefined rules, machine-learning outputs and anomaly indicators. These components contributed to a consolidated risk score.

Transactions whose scores reached a defined threshold were recorded as alerts and displayed on a web-based compliance dashboard. The dashboard showed transaction details, risk level and contributing indicators. Authorised users could review an alert, add notes and mark it as resolved or escalated. The system was intended to support a human reviewer; it was not intended to establish guilt, access live banking systems, freeze accounts or file reports automatically with the FIU.

The contribution of the proposed work was the integration of simulation, hybrid risk assessment, explainable alerts and basic compliance-case handling in one Zimbabwe-focused educational prototype. Controlled model and system results would be interpreted only within the limits of the simulated test data.

### 2.4.1 Feasibility Analysis

#### 2.4.1.1 Technical Feasibility

The system was technically feasible because it used accessible tools and existing hardware. Python supported transaction generation, feature engineering and machine-learning integration through pandas, NumPy and scikit-learn. Flask and Flask-SocketIO supported the web interface and live updates, while SQLite supported local storage. An Intel Core i5 laptop with 16 GB RAM and a 512 GB SSD was adequate for local simulation, model training and functional testing.

The main technical risks were imperfect data realism, false positives or false negatives, and poor performance at production-scale volume. They were managed by using a controlled dataset, testing modules independently, retaining rules as a complementary signal and keeping a human in the review loop. Production deployment was outside the project scope.

#### 2.4.1.2 Economic Feasibility

The prototype was economically feasible because it used existing hardware and predominantly open-source software. Python, Flask, scikit-learn, pandas, NumPy, Bootstrap and SQLite required no licence fees for this use. Main costs were the students' time, internet access, electricity and any optional demonstration hosting. The benefit was an affordable, reusable learning artefact that enabled safe experimentation without confidential banking data. A commercial implementation would require a separate cost analysis for secure hosting, integration, governance, staff training and maintenance.

#### 2.4.1.3 Social Feasibility

The system was socially feasible because it supported compliance users rather than replacing their judgement. Simulated data protected customer privacy, while explanations and notes enabled accountable review. Risks of bias and over-reliance on automation were reduced by presenting outputs as alerts, retaining human decisions and limiting the work to controlled scenarios. Any real-world use would require fairness evaluation, governance policies and user testing.

#### 2.4.1.4 Operational Feasibility

The workflow was operationally feasible for a prototype: generate a transaction, assess risk, create an alert where required, review it on the dashboard and record the outcome. The web interface could be accessed through an ordinary browser, while roles limited case actions to authorised users. The prototype did not depend on integration with live banking systems, external watchlists or FIU reporting. Live deployment would require secure integration, alert-management procedures, audit controls, staff training and institutional approval.

#### 2.4.1.5 Overview of Feasibility Study

Overall, the work was feasible within the planned 25 weeks. The selected tools, available hardware and simulated-data approach made development manageable, affordable and ethically appropriate. Excluding live customer data, production deployment and automated reporting preserved a realistic undergraduate-project scope.

## 2.5 Summary

This chapter reviewed AML monitoring approaches from international, regional and Zimbabwean perspectives. It found that rule-based monitoring remained useful but could be limited by changing and multi-step behaviour. Machine learning and anomaly detection offered complementary pattern-recognition capability, but their use required reliable data, explainability and human oversight. Synthetic data provided a suitable controlled method for testing an AML prototype where real banking data was unavailable.

The review identified a gap for a Zimbabwe-focused prototype integrating simulated transactions, real-time hybrid scoring, explainable alerts and role-based case handling. The proposed system was designed to address this gap as an educational demonstration rather than a replacement for an institutional AML programme. Chapter 3 presents the methodology, architecture, development tools, transaction simulation and model-design procedures.

## References

[1] Financial Action Task Force, *International Standards on Combating Money Laundering and the Financing of Terrorism & Proliferation: The FATF Recommendations*. Paris, France: FATF/OECD, 2023. [Online]. Available: https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Fatf-recommendations.html.

[2] R. I. T. Jensen and A. Iosifidis, “Fighting money laundering with statistics and machine learning,” *IEEE Access*, vol. 11, pp. 8889–8903, 2023, doi: 10.1109/ACCESS.2023.3239549.

[3] Financial Action Task Force, *Opportunities and Challenges of New Technologies for AML/CFT*. Paris, France: FATF/OECD, 2021. [Online]. Available: https://www.fatf-gafi.org/content/dam/fatf-gafi/guidance/Opportunities-Challenges-of-New-Technologies-for-AML-CFT.pdf.

[4] M. Weber *et al.*, “Anti-money laundering in Bitcoin: Experimenting with graph convolutional networks for financial forensics,” in *Proceedings of the KDD Workshop on Anomaly Detection in Finance*, 2019.

[5] E. Altman, J. Blanuša, L. von Niederhäusern, B. Egressy, A. Anghel and K. Atasu, “Realistic synthetic financial transactions for anti-money laundering models,” in *Advances in Neural Information Processing Systems 36*, 2023. [Online]. Available: https://arxiv.org/abs/2306.16424.

[6] IBM Research, “AMLSim: A synthetic data generator for anti-money-laundering research,” GitHub repository, 2020. [Online]. Available: https://github.com/IBM/AMLSim.

[7] Financial Intelligence Unit of Zimbabwe, “Guidelines,” 2025. [Online]. Available: https://www.fiu.co.zw/index.php/guidelines/.

[8] Financial Intelligence Unit of Zimbabwe, *Zimbabwe National Money Laundering Risk Assessment 2024*, 2025. [Online]. Available: https://www.fiu.co.zw/wp-content/uploads/2025/05/2024.pdf.

[9] Financial Intelligence Unit of Zimbabwe, *Zimbabwe National Anti-Money Laundering Strategy*, 2025. [Online]. Available: https://www.fiu.co.zw/wp-content/uploads/2025/05/National-Anti-Money-Laundering-Strategy-Final-Draft-23-April-2025.pdf.
