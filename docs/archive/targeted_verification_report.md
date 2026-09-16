# TARGETED VERIFICATION REPORT
# Class Mapping and Integration Audit

**Date:** 2026-09-02  
**Objective:** Determine whether there is a class-label mapping/prediction-output bug in the live integration

---

## 1. TRUE CLASS MAPPING

### Stage 16B Training Artifacts

**Training Code:** `train_stage16b_final_model.py` (lines 83-85)
```python
label_encoder = LabelEncoder()
label_encoder.fit(y)
y_encoded = label_encoder.transform(y)
```

**Original Labels Used During Training:**
- `normal`
- `super_suspicious`
- `suspicious`

**LabelEncoder Mapping:**
```
label_encoder.classes_ = ['normal', 'super_suspicious', 'suspicious']
```

**Frozen Model Classes:**
```
classifier.classes_ = [0 1 2]
```

**TRUE MAPPING:**
```
0 -> normal
1 -> super_suspicious
2 -> suspicious
```

**Verification:** ✅ CORRECT
- Metadata (`aml_ai_model_meta.json`) confirms: `["normal", "super_suspicious", "suspicious"]`
- Label encoder pickle (`aml_label_encoder.pkl`) confirms: `['normal', 'super_suspicious', 'suspicious']`
- Model classes: `[0 1 2]`

---

## 2. FROZEN MODEL PREDICTION

### Test Transaction 1: Suspicious Pattern (Structuring)

**Features:**
- amount: 9500
- sender_avg_amount: 3000
- sender_max_amount: 10000
- amount_to_sender_avg: 3.17
- amount_z_score: 2.0
- amount_deviation_from_baseline_30d: 0.5
- tx_frequency_7d: 30
- tx_frequency_30d: 100
- frequency_change_vs_avg_7d: 1.5
- sender_tx_count_24h: 15
- sender_volume_24h: 50000
- same_day_count: 8
- rapid_transfer_count: 5
- is_new_recipient: 0
- unique_recipients_7d: 5
- hour: 14
- is_off_hours: 0
- counterparty_change_score_7d: 0.3

**Direct Model Prediction:**
```
classifier.classes_: [0 1 2]
predict_proba(): [0.14249735 0.23355884 0.62394381]
argmax: 2
classes[argmax]: 2
LabelEncoder classes: ['normal' 'super_suspicious' 'suspicious']
Final decoded label: suspicious
```

**Result:** Model predicts "suspicious" with 62.4% confidence ✅

### Test Transaction 2: Severe Pattern

**Features (sample):**
- amount: 100000 (very large)
- amount_to_sender_avg: 33.33 (huge deviation)
- tx_frequency_7d: 200 (very high frequency)
- sender_tx_count_24h: 100 (massive 24h activity)
- same_day_count: 50 (many same-day transactions)
- rapid_transfer_count: 30 (many rapid transfers)

**Direct Model Prediction:**
```
classifier.classes_: [0 1 2]
predict_proba(): [0.69931583 0.21583756 0.08484662]
argmax: 0
Final decoded label: normal
```

**Result:** Model predicts "normal" with 69.9% confidence

---

## 3. LABEL ENCODER VERIFICATION

**Label Encoder File:** `aml_label_encoder.pkl`

**Classes:** `['normal', 'super_suspicious', 'suspicious']`

**Verification:** ✅ CORRECT
- Matches training code
- Matches metadata
- Matches expected order

---

## 4. ai_core.py MAPPING AUDIT

**File:** `ai_core.py`  
**Function:** `predict_risk_level()` (lines 424-457)

**Mapping Code:**
```python
classes = list(classifier.classes_)
best_index = int(probabilities.argmax())

if version == "16B":
    label_encoder_path = os.path.join(os.path.dirname(__file__), "aml_label_encoder.pkl")
    if os.path.exists(label_encoder_path):
        import pickle
        with open(label_encoder_path, 'rb') as f:
            label_encoder = pickle.load(f)
        predicted = label_encoder.inverse_transform([best_index])[0]
    else:
        # Fallback: map numeric to string labels
        label_map = {0: "normal", 1: "super_suspicious", 2: "suspicious"}
        predicted = label_map.get(best_index, "normal")
```

**Fallback Mapping:** `{0: "normal", 1: "super_suspicious", 2: "suspicious"}`

**Verification:** ✅ CORRECT
- Fallback mapping matches TRUE mapping
- Label encoder is loaded and used correctly
- No mapping bug detected

---

## 5. LIVE SERVER/UI FLOW

**Prediction Path:**
1. Transaction enters system
2. Feature extraction via `transaction_features()` in `ai_core.py`
3. `predict_risk_level()` called in `ai_core.py`
4. Model loaded via `load_ai_model()` in `ai_core.py`
5. Features passed to `model.predict_proba()`
6. `argmax()` finds highest probability index
7. `LabelEncoder.inverse_transform()` converts index to label
8. Confidence = `probabilities[argmax]`
9. Return `(predicted_label, confidence, anomaly_score)`
10. `server.py` `process_transaction_event()` receives prediction (line 2147)
11. **Confidence thresholds applied** (lines 2153-2159)
12. Final risk level determined
13. UI displays result

**Verification:** ✅ CORRECT
- No unexpected overwrites
- No silent fallbacks in the prediction path
- Model predictions are preserved through the flow

---

## 6. CONFIDENCE THRESHOLD AUDIT

**File:** `server.py`  
**Lines:** 2153-2159

**Threshold Logic:**
```python
confidence_threshold = 0.65  # default
if ml_level == "super_suspicious":
    confidence_threshold = 0.55
elif ml_level == "suspicious":
    confidence_threshold = 0.65
else:
    confidence_threshold = 0.75

ml_score = AI_RISK_SCORES.get(ml_level, 0) if ml_confidence >= confidence_threshold else 0
```

**Thresholds:**
- Super-suspicious: 55% confidence required
- Suspicious: 65% confidence required
- Normal: 75% confidence required

**Critical Finding:** ❌ **THRESHOLD BUG DETECTED**

The suspicious pattern prediction:
- Predicted: `suspicious`
- Confidence: `62.4%`
- Threshold required: `65%`
- **Result: REJECTED (confidence < threshold)**

The model IS predicting "suspicious" for the structuring pattern, but the confidence threshold in `server.py` line 2161 is filtering it out because 62.4% < 65%.

---

## 7. ROOT CAUSE(S)

### PRIMARY ROOT CAUSE: CONFIDENCE THRESHOLD FILTERING

**Location:** `server.py` line 2161

**Issue:** The confidence threshold logic is filtering out valid suspicious predictions.

**Evidence:**
- Model predicts "suspicious" with 62.4% confidence for structuring pattern
- Threshold requires 65% confidence for "suspicious"
- Prediction is rejected: `ml_score = 0` (line 2161)
- Final risk level becomes "normal" due to zero ML score

**Impact:** Even when the model correctly identifies suspicious transactions, they are filtered out by the confidence threshold, causing the UI to show "normal".

### SECONDARY ISSUE: MODEL HAS POOR RECALL

**Known Limitation:** The Stage 16B model has documented poor recall:
- Suspicious recall: 21.76%
- Super-suspicious recall: 25.40%

**Evidence:** The severe pattern (extremely suspicious features) is still predicted as "normal" with 69.9% confidence, indicating the model itself has poor detection capability for many suspicious patterns.

**Impact:** Even with threshold adjustments, the model will miss many suspicious transactions due to poor recall.

---

## 8. RECOMMENDED FIX — DIAGNOSIS ONLY

### Fix Option 1: Lower Confidence Threshold for Suspicious (RECOMMENDED)

**File:** `server.py`  
**Line:** 2157

**Change:**
```python
# Current:
elif ml_level == "suspicious":
    confidence_threshold = 0.65

# Recommended:
elif ml_level == "suspicious":
    confidence_threshold = 0.55  # Lower from 0.65 to 0.55
```

**Rationale:** 
- The structuring pattern prediction (62.4% confidence) would pass
- Aligns suspicious threshold with super-suspicious (55%)
- Would allow more suspicious predictions to be accepted
- Trade-off: Increased false positives

### Fix Option 2: Remove Confidence Threshold for AI-Only Mode

**File:** `server.py`  
**Lines:** 2153-2161

**Change:** When rule engine is disabled (`_RULE_ENGINE_ENABLED = False`), bypass confidence thresholds for AI predictions.

**Rationale:**
- In AI-only mode, trust the model's predictions
- No rule-based engine to provide alternative detection
- Allows model predictions to be used as-is

### Fix Option 3: Re-enable Rule-Based Engine

**Change:** Set `_RULE_ENGINE_ENABLED = True` in `transactions.py` or `server.py`

**Rationale:**
- Rules can catch patterns the ML model misses
- Complements the weak ML model
- No model changes required

---

## CONCLUSIONS

### A. MODEL QUALITY

**Is the frozen Stage 16B model genuinely producing mostly Normal predictions for suspicious-looking transactions?**

**Answer:** PARTIALLY YES

- The model DOES predict "suspicious" for some patterns (e.g., structuring: 62.4% confidence)
- The model predicts "normal" for other suspicious patterns (e.g., severe pattern: 69.9% confidence)
- The model has documented poor recall (21.76% suspicious recall, 25.40% super-suspicious recall)

**Status:** Model quality is a known limitation, but not the sole cause of "everything is normal".

### B. INTEGRATION CORRECTNESS

**Is `ai_core.py` correctly translating the frozen model's numeric predictions into labels?**

**Answer:** ✅ YES

- TRUE mapping: `0 -> normal, 1 -> super_suspicious, 2 -> suspicious`
- ai_core.py fallback mapping: `{0: "normal", 1: "super_suspicious", 2: "suspicious"}`
- Label encoder is loaded and used correctly
- No mapping bug detected

**Status:** Integration mapping is CORRECT.

### C. ROOT CAUSE SUMMARY

**Primary Issue:** Confidence threshold filtering in `server.py` line 2161
- Model predicts "suspicious" with 62.4% confidence
- Threshold requires 65% confidence
- Prediction is rejected, resulting in "normal" display

**Secondary Issue:** Model has poor recall (documented limitation)
- Many suspicious patterns are genuinely predicted as "normal"
- This is a frozen model limitation

**Integration Status:** ✅ CORRECT - No mapping bugs, no prediction overwrites

---

**TARGETED VERIFICATION COMPLETE — ROOT CAUSE IDENTIFIED — WAITING FOR APPROVAL TO APPLY FIX.**
