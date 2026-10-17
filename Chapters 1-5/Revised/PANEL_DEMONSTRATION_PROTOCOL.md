# Five-objective panel demonstration protocol

Prepare two authenticated browser sessions (customer and compliance officer), an administrator session, local MySQL `aml`, and Redis. Confirm `/health` reports V4, rules and Redis. Use a stopwatch for each row. Record actual times; do not present targets as measured results.

| Objective | Start | Stop | Target | Visible proof |
| --- | --- | --- | --- | --- |
| 1. Transaction generation module | Click the prepared ten-event generator action | Batch completion and customer history visible | 3 min | Ten saved events, declared seven routine/three suspicious scenarios, intact wallet totals and canonical history |
| 2. Real-time engine | Save an alert review status from the compliance browser on instance A | Administrator browser on instance B receives the alert update | 5 s | Redis/WebSocket delivery and isolation from the customer session |
| 3. Compliance review | Open a flagged alert | Save a review outcome | 2 min | Separate V4 and rule findings and recorded review |
| 4. Trained XGBoost and combined risk scoring | Confirm one controlled customer payment | Saved V4/rule risk state appears | 30 s | Same transaction ID, no duplicate payment, customer history status and analyst evidence |
| 5. Messaging | Send a customer message | Recipient opens it and replies; repeat for the compliance?administrator pair | 2 min per pair | Stored thread, username/account label, sent/delivered/read states and device notification if permission is granted |

For Objective 1, 70/30 is the **scenario input mix**. The number of actual V4 predictions or rule alerts may differ. Objective 4 changes balances and should use dedicated demo wallets, a unique request ID and exact before/after reconciliation. Record transaction IDs and timings on the day of presentation. Device notifications require a supported secure browser and permission; the current application tab must remain open for the live event.


For Objective 1, open Admin > Transaction Generation > Customer simulation baselines first. Record the sample count, typical amount and known recipients for each demonstrated wallet. The generator now includes registered customer accounts, so simulated payments affect their real local balances and visible histories. Select Mixed scenarios for 70/30; Routine Payments intentionally produces only routine scenarios. At least one routine payment per customer requires enough routine entries in the chosen batch. Histories with fewer than five normal/low-risk outgoing transfers are labelled limited; no established behavioural pattern should be claimed for them. Historical timing is not reproduced by immediate generation. Previously simulated history is not independent evidence of real-world behaviour.

For Objective 4, present the existing frozen training and Validation results (precision, recall, F1 and confusion matrix) before timing one committed payment. Do not retrain during the panel demonstration. The thirty-second target applies to single-payment post-commit risk assessment, not model training or a large pending queue.

Image capture locations are printed beside the figures in the revised dissertation. Figures 4.5?4.7 contain explicit insertion instructions for generator baselines/progress, two-instance Redis delivery and combined risk scoring. Replace those instructions with genuine captured images and retain numbered captions. Never replace a missing timed result with a fabricated screenshot.
