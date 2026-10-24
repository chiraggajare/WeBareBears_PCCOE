# SleepTwin: Comprehensive Project & Medical Architecture Guide

**Project:** SleepTwin — a sleep-driven cardiometabolic digital twin (Type 2 Diabetes + Hypertension)  
**Team:** WeBareBears · **Institution:** PCCOE (Pimpri Chinchwad College of Engineering)  
**Challenge:** Happiest Health Digital Twin Challenge 2026 — Phase 1  
**Licence:** MIT Open Source License  

---

## Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [Medical Dictionary: Plain-English Concepts & Numerical Thresholds](#2-medical-dictionary-plain-english-concepts--numerical-thresholds)
   - [Glucose & Metabolic Metrics](#a-glucose--metabolic-metrics)
   - [Blood Pressure & Cardiovascular Metrics](#b-blood-pressure--cardiovascular-metrics)
   - [Sleep & Wearable Sensors](#c-sleep--wearable-sensors)
   - [Pharmacology & Medication Interactions](#d-pharmacology--medication-interactions)
   - [Kidney & Lipid Laboratory Panels](#e-kidney--lipid-laboratory-panels)
   - [Genetics & Susceptibility](#f-genetics--susceptibility)
3. [Technology Stack](#3-technology-stack)
4. [System Architecture & 4-Stage Data Pipeline](#4-system-architecture--4-stage-data-pipeline)
5. [Mathematical Formulations & Physiology Modeling](#5-mathematical-formulations--physiology-modeling)
6. [Machine Learning Models, Validation & Explainability](#6-machine-learning-models-validation--explainability)
7. [Detailed Directory & File-by-File Code Breakdown](#7-detailed-directory--file-by-file-code-breakdown)
   - [Root Files](#root-files)
   - [Source Code (`src/`)](#source-code-src)
   - [Backend API (`api/`)](#backend-api-api)
   - [Frontend Web Application (`web/`)](#frontend-web-application-web)
   - [Automation Scripts (`scripts/`)](#automation-scripts-scripts)
   - [Automated Tests (`tests/`)](#automated-tests-tests)
   - [Data & Reports (`data/`, `reports/`, `docs/`)](#data--reports-data-reports-docs)
8. [The Three Clinical Personas (A, B, C Walkthrough)](#8-the-three-clinical-personas-a-b-c-walkthrough)
9. [Security Engineering & Safety Safeguards](#9-security-engineering--safety-safeguards)
10. [Execution & Verification Guide](#10-execution--verification-guide)

---

## 1. Executive Summary & Problem Statement

### The Problem
Patients managing chronic conditions like **Type 2 Diabetes (T2D)** and **Hypertension (HTN)** visit their doctor for roughly 15 minutes once every few months. In the intervening weeks and months, their day-to-day metabolic health fluctuates invisibly.

Commercial wearables (Apple Watch, Fitbit, Oura Ring) measure sleep, heart rate, and movement nightly, but they provide **generic consumer sleep scores** (e.g., *"Your sleep score is 74/100"*). They possess zero clinical context:
- They do not know the user is a 54-year-old diabetic taking metformin and a beta-blocker.
- They cannot warn the user that 4 nights of poor sleep silently reduce insulin sensitivity by 20–30%, setting off post-meal glucose spikes (> 180 mg/dL).
- They miss acute stress because **beta-blockers mask heart rate rises** (the heart rate stays flat while Heart Rate Variability drops).
- They miss **hidden sleep apnea** in patients who sleep 7.5 hours but suffer frequent nocturnal oxygen drops that trigger morning blood pressure surges (> 145 mmHg).

### The Solution: SleepTwin
SleepTwin is a virtual, computational copy of each patient. It continuously fuses two data streams:
1. **Static Health Record (EHR):** Demographics, clinic blood pressure, diagnostic histories, kidney/lipid labs, medications, and genetic susceptibility markers.
2. **Dynamic Wearable Stream:** 5-minute Continuous Glucose Monitoring (CGM), sleep duration, hypnogram sleep stages, nocturnal Heart Rate Variability (HRV), Resting Heart Rate (RHR), and Oxygen Desaturation Index (ODI).

### What SleepTwin Does
1. **Learns a 14-Day Personal Normal:** Calculates baseline means and standard deviations for every individual wearable parameter.
2. **Predicts Next-Day Clinical Risks:** Issues daily forecasts for tomorrow’s glucose peak crossing 180 mg/dL and morning systolic BP exceeding 145 mmHg.
3. **Issues a 2-Hour Real-Time Alert:** Evaluates live CGM trends to warn of impending glucose spikes 120 minutes ahead (median warning lead time of 70 minutes).
4. **Explains Every Prediction:** Employs SHAP game-theoretic feature attribution to translate machine learning outputs into natural language clinical explanations.
5. **Enables What-If Counterfactual Sandbox:** In ~15 ms, doctors can test interventions (e.g., adding 2 hours of sleep, adjusting bedtime, or adding CPAP therapy) to see the projected impact on tomorrow’s glucose curves and blood pressure before prescribing changes.

---

## 2. Medical Dictionary: Plain-English Concepts & Numerical Thresholds

Below is a complete glossary of every medical term used in SleepTwin, how it works in the human body, its numerical diagnostic thresholds, and its exact role in the digital twin.

### A. Glucose & Metabolic Metrics

#### 1. Type 2 Diabetes Mellitus (T2D)
- **Plain English:** A chronic condition where the body’s cells become resistant to insulin, and the pancreas cannot produce enough insulin to overcome this resistance, causing glucose to build up in the bloodstream.
- **Numerical Diagnostics:**
  - **Normal:** HbA1c < 5.7% and Fasting Blood Glucose < 100 mg/dL.
  - **Prediabetes:** HbA1c 5.7% – 6.4% or Fasting Blood Glucose 100 – 125 mg/dL.
  - **Type 2 Diabetes:** HbA1c ≥ 6.5% or Fasting Blood Glucose ≥ 126 mg/dL.
- **Use in SleepTwin:** Governs baseline pancreatic beta-cell sensitivity ($\beta$) and baseline insulin sensitivity ($SI_0$). Diabetic patients experience sharper glucose peaks after poor sleep.

#### 2. HbA1c (Glycated Hemoglobin)
- **Plain English:** A blood test measuring the percentage of hemoglobin proteins in red blood cells that are coated with sugar. Because red blood cells live for about 3 months, it reflects average blood sugar control over the preceding 8–12 weeks.
- **Numerical Diagnostic Scale:**
  - `< 5.7%`: Normal healthy glycemic control.
  - `5.7% – 6.4%`: Prediabetes.
  - `6.5% – 7.0%`: Controlled diabetes target for most adults.
  - `> 8.0%`: Poor glycemic control; heightened risk of vascular complications.
- **Use in SleepTwin:** Primary EHR feature. Serves as a major driver for the baseline glucose level ($G_b$) and compounds the negative impact of sleep debt (`debt_x_hba1c` interaction).

#### 3. CGM (Continuous Glucose Monitoring)
- **Plain English:** A small wearable sensor inserted under the skin that measures glucose in the interstitial fluid every 5 minutes throughout the day and night.
- **Numerical Scale:** 
  - Expressed in milligrams per deciliter (mg/dL).
  - Normal fasting: 70–99 mg/dL.
  - Normal post-meal: < 140 mg/dL.
  - Clinical spike alert threshold: **> 180 mg/dL** (the primary next-day target in SleepTwin).
- **Use in SleepTwin:** Generated at 5-minute intervals (288 readings/day) using the Bergman minimal model. Used to evaluate Time-in-Range, 24-hour peak glucose, and 2-hour advance alerts.

#### 4. TIR (Time in Range)
- **Plain English:** The percentage of time in a 24-hour period that a patient's glucose stays within the safe target zone (70 to 180 mg/dL).
- **Numerical Scale:**
  - `> 70%`: Clinical target for diabetics (equates to ~17 hours a day in range).
  - `< 50%`: High glycemic instability; frequent hyper- or hypoglycemia.
- **Use in SleepTwin:** Summarized daily (`tir_prev_24h`) as a context feature for the next-day forecast.

#### 5. Fasting Plasma Glucose (FPG)
- **Plain English:** Blood sugar level measured after an overnight fast of at least 8 hours.
- **Numerical Scale:** Normal < 100 mg/dL; Prediabetes 100–125 mg/dL; Diabetes ≥ 126 mg/dL.
- **Use in SleepTwin:** Stored in the static EHR profile. Shrunk by 55% toward 90 mg/dL to calibrate the baseline free-living CGM parameter ($G_b$).

#### 6. Insulin Sensitivity Index ($SI$)
- **Plain English:** A physiological measure of how effectively insulin clears glucose from the blood. High sensitivity means small amounts of insulin clear glucose easily; low sensitivity (insulin resistance) means glucose lingers at high levels.
- **Numerical Scale:** In the Bergman model, reference healthy $SI_{\text{ref}} \approx 6.0 \times 10^{-4}\text{ min}^{-1}/(\mu\text{U/mL})$. In SleepTwin, sleep debt lowers $SI$ by 20–30%.
- **Use in SleepTwin:** Dynamically recomputed every single day in `src/physiology.py`. Connects sleep loss to glucose dynamics.

---

### B. Blood Pressure & Cardiovascular Metrics

#### 1. SBP & DBP (Systolic & Diastolic Blood Pressure)
- **Plain English:** Blood pressure is written as Systolic / Diastolic (e.g., 120/80 mmHg).
  - **Systolic (SBP):** Pressure in the arteries when the heart contracts.
  - **Diastolic (DBP):** Resting pressure in arteries between heartbeats.
- **Numerical Diagnostics (AHA/ACC Guidelines):**
  - **Normal:** SBP < 120 and DBP < 80 mmHg.
  - **Elevated:** SBP 120–129 and DBP < 80 mmHg.
  - **Stage 1 Hypertension:** SBP 130–139 or DBP 80–89 mmHg.
  - **Stage 2 Hypertension:** SBP ≥ 140 or DBP ≥ 90 mmHg.
  - **SleepTwin Morning Alert Threshold:** **Morning SBP > 145 mmHg**.
- **Use in SleepTwin:** Clinic baseline is held in the EHR. Morning SBP is predicted using sleep fragmentation, sleep debt, nocturnal oxygen dips, and antihypertensive medication status.

#### 2. HTN (Hypertension)
- **Plain English:** Chronic high blood pressure causing long-term strain on arteries, heart, and kidneys.
- **Numerical Scale:** Clinical diagnosis confirmed when SBP ≥ 140 mmHg or DBP ≥ 90 mmHg on repeated clinic visits, or when prescribed antihypertensive medication.
- **Use in SleepTwin:** Core comorbidity present in ~45% of the virtual cohort. Interacts with nocturnal hypoxia (`odi_x_has_htn`).

---

### C. Sleep & Wearable Sensors

#### 1. TST (Total Sleep Time)
- **Plain English:** The actual amount of time spent sleeping in hours, excluding time spent falling asleep or awake during the night.
- **Numerical Scale:**
  - Adult healthy range: 7.0 – 9.0 hours.
  - Chronic short sleep: < 6.0 hours.
  - Severe sleep restriction: ≤ 5.0 hours.
- **Use in SleepTwin:** Recorded nightly. Evaluated against each patient's 14-day personal baseline ($TST_{\text{base}}$) to generate daily sleep debt.

#### 2. Sleep Debt
- **Plain English:** The accumulated deficit when a person sleeps less than their body's biological requirement across several consecutive nights.
- **Numerical Scale:** Calculated in SleepTwin with an exponential 7-day memory decay factor of 0.75:
  $$\text{debt}_t = \sum_{k=0}^{6} \max(0, \text{TST}_{\text{base}} - \text{TST}_{t-k}) \cdot (0.75)^k$$
  - `0.0 hours`: Fully rested.
  - `> 3.0 hours`: Moderate cumulative metabolic impairment.
  - `> 6.0 hours`: Severe metabolic stress (~25% drop in insulin sensitivity).
- **Use in SleepTwin:** One of the strongest predictive features in next-day glucose and blood pressure models.

#### 3. WASO (Wake After Sleep Onset)
- **Plain English:** The total minutes spent awake in bed between the initial moment of falling asleep and the final morning awakening.
- **Numerical Scale:**
  - `< 20 – 30 minutes`: Normal sleep efficiency.
  - `> 60 minutes`: Significant sleep fragmentation and disturbance.
  - `> 90 minutes`: Severe nocturnal fragmentation (frequent in sleep apnea).
- **Use in SleepTwin:** Directly impairs insulin sensitivity and elevates morning blood pressure ($+3\text{ mmHg per hour of WASO}$).

#### 4. Sleep Stages (Deep, REM, Light, Wake)
- **Plain English:**
  - **Deep Sleep (Slow Wave Sleep / N3):** Restorative stage that repairs tissue, releases growth hormone, and restores autonomic balance. Usually front-loaded in the first third of the night.
  - **REM (Rapid Eye Movement):** Dreaming stage crucial for memory processing and cognitive health; grows longer in the final cycles of the night.
  - **Light Sleep (N1 + N2):** Transition stage making up the bulk of the night.
- **Numerical Distribution in Healthy Adults:**
  - Deep Sleep: 10% – 25% of total sleep time.
  - REM Sleep: 18% – 25% of total sleep time.
  - Light Sleep: 50% – 60% of total sleep time.
- **Use in SleepTwin:** Synthesized into 5-minute epoch hypnograms. A downward trend in deep sleep over 7 days (`deep_pct_7d_slope`) flags cumulative autonomic strain.

#### 5. ODI (Oxygen Desaturation Index) & OSA (Obstructive Sleep Apnea)
- **Plain English:**
  - **OSA:** A sleep breathing disorder where the upper airway repeatedly collapses during sleep, stopping airflow.
  - **ODI:** The number of times blood oxygen saturation ($SpO_2$) drops by 3% or 4% or more per hour of sleep.
- **Numerical Diagnostic Scale for OSA (based on ODI/AHI):**
  - `< 5 events/hour`: Normal.
  - `5 – 14 events/hour`: Mild Sleep Apnea.
  - `15 – 29 events/hour`: Moderate Sleep Apnea (SleepTwin flags as potential hidden OSA).
  - `≥ 30 events/hour`: Severe Sleep Apnea.
- **Use in SleepTwin:** Used to uncover undiagnosed apnea (Persona B). High ODI directly elevates morning SBP ($+0.55\text{ mmHg per ODI unit}$).

#### 6. HRV (Heart Rate Variability) & RMSSD
- **Plain English:** The variation in time (measured in milliseconds) between consecutive heartbeats. Contrary to intuition, a healthy heart does not tick like a metronome; higher variability indicates a relaxed, adaptable parasympathetic nervous system. When the body experiences stress, sleep debt, or hypoxia, HRV drops.
- **RMSSD:** Root Mean Square of Successive Differences between normal heartbeats; the gold standard time-domain metric used by smartwatches.
- **Numerical Scale:**
  - Varies widely by age: young adults ~50–90 ms; older adults ~20–40 ms.
  - Therefore, absolute numbers are misleading. SleepTwin relies strictly on **z-score deviation from the patient's own 14-day mean**:
    - `0.0`: Personal normal.
    - `-1.0 SD`: Noticeable autonomic strain.
    - `≤ -2.0 SD` (or a drop of > 20%): Acute physiological stress.
- **Use in SleepTwin:** Key indicator for sympathetic stress, especially vital when heart rate is masked by medication.

#### 7. RHR (Resting Heart Rate)
- **Plain English:** The number of heart contractions per minute when the body is at complete rest during sleep.
- **Numerical Scale:**
  - Athlete: 40–55 bpm.
  - Typical adult: 60–80 bpm.
  - Elevated stress/tachycardia: > 85 bpm.
- **Use in SleepTwin:** Evaluated as $\Delta RHR$ from baseline. Typically rises by 3–8 bpm under sleep deprivation.

#### 8. CPAP (Continuous Positive Airway Pressure)
- **Plain English:** A medical device delivering pressurized room air through a mask to prevent airway collapse during sleep.
- **Numerical Modeling in What-If:**
  - Reduces ODI by **80%** ($\text{ODI}_{\text{new}} = \text{ODI} \times 0.2$).
  - Reduces nocturnal wakefulness (WASO) by **40%** ($\text{WASO}_{\text{new}} = \text{WASO} \times 0.6$).

---

### D. Pharmacology & Medication Interactions

#### 1. Beta-Blockers (e.g., Metoprolol) & The "Masking" Phenomenon
- **Plain English:** A class of cardiovascular medications that block adrenaline receptors on the heart, keeping the heart rate low and lowering blood pressure.
- **The Masking Problem:** When an unmedicated person is sleep-deprived, sympathetic stress causes their resting heart rate to jump by 5–10 bpm. In a patient on a beta-blocker, the medication **artificially holds their resting heart rate down**.
- **Numerical Formulation in SleepTwin:**
  $$\Delta\text{RHR}_{\text{observed}} = \min(\text{rise}, 3.0\text{ bpm})$$
  While the resting heart rate only ticks up by 1–3 bpm, **HRV still drops by 20–35%**. SleepTwin detects this dissociation and alerts the doctor that heart rate cannot be relied upon to gauge stress.

#### 2. Metformin
- **Plain English:** The first-line oral medication for Type 2 Diabetes. It lowers glucose production in the liver and improves muscle insulin sensitivity.
- **Numerical Formulation:** Modeled as providing a $+10\%$ boost to daily insulin sensitivity ($b_2 = 0.10$).

#### 3. SGLT2 Inhibitors (e.g., Empagliflozin)
- **Plain English:** Modern diabetes medications that force the kidneys to excrete excess blood glucose into urine.
- **Numerical Formulation:** Modeled as reducing basal glucose levels by ~6 mg/dL through continuous glycosuria.

#### 4. ACE Inhibitors (e.g., Lisinopril)
- **Plain English:** Blood pressure medications that relax blood vessels by blocking the formation of Angiotensin II.
- **Numerical Formulation:** Modeled as lowering baseline morning systolic BP by 6 mmHg ($c_4 = 6.0$).

#### 5. Sulfonylureas (e.g., Glipizide)
- **Plain English:** Diabetes medications that trigger pancreatic beta-cells to secrete extra insulin regardless of blood sugar levels.
- **Numerical Formulation:** Increases pancreatic responsivity factor $\beta$ by $+25\%$.

---

### E. Kidney & Lipid Laboratory Panels

#### 1. eGFR (Estimated Glomerular Filtration Rate) & CKD-EPI 2021
- **Plain English:** A measure of how efficiently the kidneys filter metabolic waste from the blood, calculated from serum creatinine, age, and sex.
- **Numerical Scale (mL/min/1.73m²):**
  - `≥ 90`: Normal kidney function.
  - `60 – 89`: Mild kidney impairment.
  - `30 – 59`: Moderate Chronic Kidney Disease (Stage 3).
  - `< 15`: Kidney failure.
- **Use in SleepTwin:** Computed directly from raw NHANES creatinine values using the race-free 2021 CKD-EPI equation (*Inker et al., NEJM 2021*).

#### 2. Lipid Profile (LDL, HDL, Triglycerides)
- **Plain English:**
  - **LDL ("Bad" Cholesterol):** Contributes to arterial fatty buildup; target < 100 mg/dL (or < 70 mg/dL in diabetics).
  - **HDL ("Good" Cholesterol):** Transports cholesterol away from arteries back to the liver; healthy level > 40 mg/dL (men) or > 50 mg/dL (women).
  - **Triglycerides:** Fat in the bloodstream; normal < 150 mg/dL.
- **Use in SleepTwin:** Integrated into the static EHR risk profile to assess overall cardiometabolic comorbidity.

---

### F. Genetics & Susceptibility

*Note: In SleepTwin, all genetic values are computationally simulated to represent well-documented physiological effects.*

#### 1. TCF7L2 (Transcription Factor 7-Like 2, rs7903146)
- **Plain English:** The strongest known genetic risk gene for Type 2 Diabetes. The risk allele (T) impairs insulin secretion from pancreatic beta-cells.
- **Numerical Modeling:**
  - South Asian allele frequency: $29.9\%$ (from 1000 Genomes Phase 3 SAS).
  - Patients possess 0, 1, or 2 risk alleles.
  - Each risk allele reduces pancreatic insulin secretion response $\beta$ by $5\%$ and baseline insulin sensitivity $SI_0$ by $3\%$.

#### 2. MTNR1B (Melatonin Receptor 1B, rs10830963)
- **Plain English:** A gene regulating melatonin receptors in the pancreas. Carriers of the G risk allele experience disrupted glucose metabolism if they eat late at night or delay their bedtime while melatonin is active.
- **Numerical Modeling:**
  - South Asian allele frequency: $42.6\%$.
  - Modeled as an interaction term: $g = 0.30$. When bedtime shifts by $\ge 1.5\text{ hours}$, carriers suffer an extra $30\%$ drop in insulin sensitivity.

#### 3. PRS (Polygenic Risk Score for T2D)
- **Plain English:** A single number aggregating the cumulative effect of thousands of small genetic variants across the whole genome.
- **Numerical Scale:** Normalized as a statistical z-score ($\text{mean} = 0$, $\text{SD} = 1$). A score of $+1.6$ represents the top 5% of genetic susceptibility.

---

## 3. Technology Stack

| Layer | Tools | Version | Purpose in SleepTwin |
|---|---|---|---|
| **Language Runtime** | Python | 3.11 – 3.14 | Core computation, simulation, ML models, and backend server |
| **Data Architecture** | Pandas, PyArrow | 3.0, 26.0 | Columnar on-disk Parquet storage; fast loading without database engines |
| **Numerical Mathematics** | NumPy, SciPy | 2.4, 1.17 | Vectorized Euler ODE integration and non-parametric statistics |
| **Machine Learning** | LightGBM, Scikit-Learn | 4.7, 1.9 | Monotone-constrained gradient boosted trees and GroupKFold cross-validation |
| **Model Interpretability** | SHAP | 0.51 | TreeExplainer game-theoretic feature attribution |
| **API Framework** | FastAPI, Uvicorn, Pydantic | 0.146, 0.54, 2.14 | High-performance asynchronous REST API, typing, and OpenAPI generation |
| **Frontend Framework** | React, TypeScript, Vite | 19.3, 6.0, 8.0 | Component-driven UI, typed client, and lightning-fast build tooling |
| **Styling & Visualization** | Tailwind CSS, Recharts | 4.0, 3.0 | Modern utility-first CSS, time-series line charts, hypnograms, gauges |
| **Automated Testing** | Pytest, HTTPX | 9.1, 0.28 | 37 unit, integration, and security tests |
| **Asset Generation** | ReportLab, Python-PPTX | 5.0, 1.0 | Programmatic compilation of architecture diagrams and slide decks |

---

## 4. System Architecture & 4-Stage Data Pipeline

The SleepTwin system operates across four coordinated stages:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        STAGE 1: OPEN DATA POOL                         │
│  CDC NHANES (US Adult Health Surveys) + LifeSnaps (Fitbit Daily Export)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Calibrates Joint Distributions
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   STAGE 2: VIRTUAL COHORT SIMULATOR                    │
│  300 Patients x 21 Days:                                               │
│  • Synthetic EHR (Labs, Meds, Diagnoses, Simulated Genetics)           │
│  • Wearable Stream (Sleep stages, HRV, RHR, ODI, Steps)                │
│  • Physiology Engine (Bergman Minimal Model 5-min CGM & Morning BP)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Writes Parquet Tables
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        STAGE 3: THE TWIN BRAIN                         │
│  • Days 1–14: Learns Personal Normal Baseline (Mean ± 1 SD)           │
│  • Days 15–21: 5-Fold GroupKFold LightGBM Models (Monotone Constraints)│
│  • Real-time 2-Hour Ahead Glucose Spike Detector                       │
│  • SHAP Attribution mapped to Plain-English Reasons                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Serves REST API Contracts
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      STAGE 4: DOCTOR'S DASHBOARD                       │
│  • Clinical Patient Triage Table (Sorted by Fused Risk)                │
│  • Overview Screen (Gauges, Trends, 2-Hr Alerts, Beta-Blocker Warning) │
│  • What-If Counterfactual Sandbox (15 ms live simulation)              │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Stage 1 (Open Calibration):** Samples joint real-world physiological distributions from CDC NHANES and Fitbit distributions from LifeSnaps.
2. **Stage 2 (Cohort Simulation):** Generates 300 virtual individuals across 21 days (6,300 patient-days). Days 1–14 act as the calibration baseline; days 15–21 serve as prediction days.
3. **Stage 3 (Twin Intelligence):** Computes personalized deviation z-scores, tracks cumulative sleep debt, fits LightGBM classifiers, and maps SHAP values into clinical explanations.
4. **Stage 4 (Doctor Dashboard):** Delivers an interactive clinical decision interface featuring real-time risk triage, multi-day trend graphs, and an instant What-If simulator.

---

## 5. Mathematical Formulations & Physiology Modeling

### A. Sleep Debt Formula
$$\text{debt}_t = \sum_{k=0}^{6} \max(0, \text{TST}_{\text{base}} - \text{TST}_{t-k}) \cdot (0.75)^k$$
Deficits decay exponentially over 7 nights, reflecting the human body's recovery timeline.

### B. Daily Insulin Sensitivity Formula
$$SI_t = SI_0 \cdot \exp\Big(-a_1 \cdot \text{debt}_t - a_2 \cdot |\Delta\text{bedtime}_t| \cdot (1 + g \cdot \text{MTNR1B}) - a_3 \cdot \frac{\text{WASO}_t}{60}\Big) \cdot (1 + b_1 \cdot \Delta\text{steps}_{t-1} + b_2 \cdot \text{metformin}) \cdot \epsilon$$
- $a_1 = 0.042$: Calibrated so that 4 nights of 5 hours of sleep produces a **25% decline in insulin sensitivity**.
- $a_2 = 0.060$: Quantifies the insulin resistance penalty of shifting sleep timing.
- $g = 0.30$: Magnifies timing penalties in *MTNR1B* risk carriers.
- $a_3 = 0.050$: Accounts for sleep disruption from nocturnal awakenings.
- $b_1 = 0.020$: Rewards physical activity above personal average.
- $b_2 = 0.10$: Accounts for the sensitizing effect of metformin.

### C. Glucose Kinetics: Bergman Minimal Model
Integrated with 1-minute fixed-step Euler integration:
$$\frac{dG(t)}{dt} = -(p_1 + X(t)) \cdot G(t) + p_1 \cdot G_b + \frac{R_a(t)}{V}$$
$$\frac{dX(t)}{dt} = -p_2 \cdot X(t) + p_3 \cdot (I(t) - I_b) \quad \text{where } p_3 = SI_t \cdot p_2$$
$$I(t) = I_b + \beta \cdot \max(0, G(t) - G_b)$$
- $p_1 = 0.005\text{ min}^{-1}$: Glucose effectiveness (clearance at basal insulin).
- $p_2 = 0.025\text{ min}^{-1}$: Remote insulin decay rate.
- $R_a(t)$: Rate of meal glucose appearance modeled via Gamma absorption:
  $$R_a(t) = f_{\text{abs}} \cdot \text{carbs} \cdot 1000 \cdot \frac{t}{\tau^2} \cdot \exp(-t/\tau)$$
  where bioavailability $f_{\text{abs}} = 0.9$ and absorption time constant $\tau = 60\text{ minutes}$.

### D. Morning Systolic Blood Pressure Rule
$$\text{SBP}_{\text{morning}} = \text{SBP}_{\text{clinic}} + c_1 \cdot \text{ODI} + c_2 \cdot \text{debt} + c_3 \cdot \frac{\text{WASO}}{60} - c_4 \cdot \text{on\_ACEi} + \text{offset}_{\text{home-vs-clinic}} + \mathcal{N}(0, 6)$$
- $c_1 = 0.55\text{ mmHg/ODI}$: Pressor effect of recurrent intermittent hypoxia.
- $c_2 = 1.10\text{ mmHg/hour}$: Sympathetic activation from sleep debt.
- $c_3 = 3.00\text{ mmHg/hour}$: Vascular reactivity from sleep fragmentation.
- $c_4 = 6.00\text{ mmHg}$: Protective reduction from ACE-inhibitor therapy.

---

## 6. Machine Learning Models, Validation & Explainability

### A. Next-Day Prediction Models
- **Algorithm:** LightGBM Classifier with Monotone Constraints.
- **Constraints Applied:** 
  - Monotonically Increasing (+1): `sleep_debt_7d`, `short_nights_4d`, `bedtime_shift`, `waso_3d_mean`, `odi_z`, `hba1c`, `debt_x_hba1c`.
  - Monotonically Decreasing (-1): `tst_z`, `hrv_z`.
  - **Clinical Guarantee:** Ensuring that adding sleep debt or shifting bedtime can *never* paradoxically reduce risk in What-If calculations.
- **Cross-Validation:** 5-fold `GroupKFold` grouped strictly by `patient_id`. Each patient is evaluated out-of-fold by a model that never trained on their data.
- **3-Tier Ablation Benchmark:**
  - **Tier 1 (EHR-Only):** AUROC $0.912$, AUPRC $0.779$
  - **Tier 2 (Wearables-Only):** AUROC $0.924$, AUPRC $0.809$
  - **Tier 3 (Fused Digital Twin):** **AUROC $0.931$, AUPRC $0.821$**
  - **Within Diabetics Only:** AUROC jumps from $0.85$ (EHR alone) to **$0.88$ (Fused Twin)**.

### B. Short-Horizon (2-Hour Spike) Detector
- Evaluates waking hours (07:00–21:00) when glucose is currently in range (< 160 mg/dL).
- **Inputs:** Current CGM, 30-min slope, 60-min slope, meal carbs, minutes since last meal, 24-hr CGM CV, last night’s sleep debt, last night’s HRV z-score, HbA1c, PRS, and medications.
- **Performance:** **AUROC $0.95$** (vs. $0.79$ for a simple linear trend arrow).
- Successfully detects 60% of upcoming glucose spikes with a **median advance warning of 70 minutes**.

### C. SHAP Explainability Engine
Rather than presenting raw mathematical SHAP coefficients to clinicians, SleepTwin groups related features into plain-English mechanisms:
- `short_sleep` $\rightarrow$ *"4 short nights in a row (last 5.0 h vs usual 7.4 h)"*
- `hrv` $\rightarrow$ *"HRV down 32% from personal normal - beta-blocker hides the heart-rate signal"*
- `apnea` $\rightarrow$ *"Frequent oxygen dips at night (~22/hr) - possible sleep apnea"*
- `control` $\rightarrow$ *"Made worse by high HbA1c (8.1%)"*

---

## 7. Detailed Directory & File-by-File Code Breakdown

### Root Files
- [`run.py`](../run.py): Cross-platform launcher. Checks dependencies, runs the data pipeline, starts the Uvicorn server, detects local IP for mobile LAN testing (`--lan`), and opens the browser (`--open`).
- [`requirements.txt`](../requirements.txt): Exact pinned dependencies.
- [`pytest.ini`](../pytest.ini): Configures test execution flags.
- [`LICENSE`](../LICENSE): MIT Open Source License.

### Source Code (`src/`)
- [`src/config.py`](../src/config.py): Defines global constants (300 patients, 21 days, thresholds of 180 mg/dL and 145 mmHg, risk bands, dates, and directory paths).
- [`src/calibration.py`](../src/calibration.py): Reads raw CDC NHANES XPT files and LifeSnaps Fitbit CSVs. Computes CKD-EPI eGFR and builds joint distribution pools.
- [`src/profiles.py`](../src/profiles.py): Synthesizes 300 EHR profiles. Samples South Asian allele frequencies (*TCF7L2*, *MTNR1B*), diagnoses, medications, prior labs, and scripts the 3 primary demo personas.
- [`src/wearables.py`](../src/wearables.py): Generates 21 days of sleep, heart, and step streams. Implements `night_heart` for autonomic modeling and `hypnogram` for 5-minute sleep stages.
- [`src/physiology.py`](../src/physiology.py): Core mathematical formulas: `sleep_debt`, `si_series`, `simulate_glucose` (Bergman ODE integration), and `morning_sbp`.
- [`src/generate_cohort.py`](../src/generate_cohort.py): Orchestrates the complete 300-patient simulation and saves processed Parquet files into `data/processed/`.
- [`src/features.py`](../src/features.py): Derives 14-day baseline means/SDs and generates daily z-score features (`tst_z`, `hrv_z`, `odi_z`, `debt_x_hba1c`, etc.).
- [`src/train.py`](../src/train.py): Trains the 5-fold cross-validated LightGBM next-day models, runs the 3-tier ablation study, and computes SHAP importances.
- [`src/short_horizon.py`](../src/short_horizon.py): Constructs hourly sample windows and trains the 2-hour-ahead glucose spike model.
- [`src/explain.py`](../src/explain.py): Maps numerical SHAP values into categorized, natural language clinical explanations.
- [`src/twin.py`](../src/twin.py): The digital twin engine. Keeps models in memory, scores patients out-of-fold, and powers the 15 ms What-If simulation.
- [`src/validate_lifesnaps.py`](../src/validate_lifesnaps.py): Runs paired Wilcoxon signed-rank validation on 38 real Fitbit users from the LifeSnaps dataset.
- [`src/integrity.py`](../src/integrity.py): Computes and verifies SHA-256 hashes of all trained `.joblib` model files before unpickling.
- [`src/report.py`](../src/report.py): Auto-generates `reports/results.md` directly from pipeline output metrics.
- [`src/pipeline.py`](../src/pipeline.py): Master CLI script running calibration $\rightarrow$ simulation $\rightarrow$ features $\rightarrow$ training $\rightarrow$ validation.

### Backend API (`api/`)
- [`api/main.py`](../api/main.py): FastAPI web server. Defines typed endpoints, rate limiters, security headers, static SPA routing, and Pydantic validation schemas.
- `api/mock/`: Contains frozen mock JSON payloads (`patients.json`, `patient_A.json`, `trends_A.json`, `what_if_A.json`) for offline frontend development.

### Frontend Web Application (`web/`)
- [`web/src/App.tsx`](../web/src/App.tsx): Main application layout, routing, header navigation, persona switcher (A, B, C), and global safety banners.
- [`web/src/api.ts`](../web/src/api.ts): Typed TypeScript client handling API requests to the backend.
- [`web/src/components/ui.tsx`](../web/src/components/ui.tsx): UI components: Gauge dials, Risk badges, Alert cards, Modals, and Simulated Data chips.
- [`web/src/lib/state.ts`](../web/src/lib/state.ts): Persistent state context storing the currently active patient ID.
- **Pages:**
  - [`web/src/pages/PatientsPage.tsx`](../web/src/pages/PatientsPage.tsx): Clinical triage list sorted by risk level with search and filter capabilities.
  - [`web/src/pages/OverviewPage.tsx`](../web/src/pages/OverviewPage.tsx): Single-patient deep dive: EHR summary, dual risk gauges, SHAP reasons, 2-hour alert banner, and beta-blocker notices.
  - [`web/src/pages/TrendsPage.tsx`](../web/src/pages/TrendsPage.tsx): Time-series visualizations showing 21-day trajectories alongside green personal-normal baseline bands.
  - [`web/src/pages/WhatIfPage.tsx`](../web/src/pages/WhatIfPage.tsx): Interactive scenario sandbox with sleep duration sliders, bedtime shift controls, CPAP toggles, and before/after glucose curves.
  - [`web/src/pages/AboutPage.tsx`](../web/src/pages/AboutPage.tsx): Interactive documentation detailing formulas, models, ablation results, and literature citations.
  - [`web/src/pages/AbbreviationsPage.tsx`](../web/src/pages/AbbreviationsPage.tsx): Searchable clinical acronym dictionary.

### Automation Scripts (`scripts/`)
- [`scripts/download_data.py`](../scripts/download_data.py): Downloads open datasets from the CDC and Zenodo using HTTP range requests with SHA-256 validation.
- [`scripts/make_docs.py`](../scripts/make_docs.py): Programmatically builds `presentation.pptx`, `presentation.pdf`, and `architecture.pdf`.
- [`scripts/take_screenshots.py`](../scripts/take_screenshots.py): Automates headless browser screenshots of dashboard views.
- [`scripts/export_mocks.py`](../scripts/export_mocks.py): Refreshes `api/mock/*.json` files from a running backend instance.

### Automated Tests (`tests/`)
- [`tests/test_sleeptwin.py`](../tests/test_sleeptwin.py): Verifies physiology math (25% SI drop), absence of cross-fold leakage, and API endpoint contracts.
- [`tests/test_security.py`](../tests/test_security.py): Verifies security headers, CORS origin restrictions, path traversal prevention, request body limits, rate limiting, and model integrity checking.

### Data & Reports (`data/`, `reports/`, `docs/`)
- `data/raw/`: Storage directory for raw NHANES XPT files and LifeSnaps daily CSVs.
- `data/processed/`: Columnar Parquet files (`profiles.parquet`, `cgm.parquet`, `nights.parquet`, `daily.parquet`).
- `reports/`: JSON metric summaries and the generated results document ([`reports/results.md`](../reports/results.md)).
- `docs/`: System documentation, architecture diagrams, and slide decks.

---

## 8. The Three Clinical Personas (A, B, C Walkthrough)

| Feature | Persona A: Rajesh Iyer | Persona B: Sunita Kulkarni | Persona C: Arjun Menon |
|---|---|---|---|
| **Demographics** | 54-year-old Male, BMI 29.4 | 41-year-old Female, BMI 32.0 | 27-year-old Male, BMI 21.8 |
| **Medical Profile** | T2D (HbA1c 8.1%), HTN, Metformin + Metoprolol | Prediabetes (HbA1c 6.1%), Undiagnosed OSA | Healthy, Active Runner, Normal Labs |
| **Genetics** | *TCF7L2* = 2, *MTNR1B* = 1, High PRS (+1.6) | *TCF7L2* = 1, *MTNR1B* = 1, PRS (+0.4) | *TCF7L2* = 0, *MTNR1B* = 0, Low PRS (-1.1) |
| **Wearable Pattern** | 4 nights of ~5.0 h sleep, bedtime +2 h later, HRV -32%, RHR only +3 bpm | 7.2 h sleep nightly, WASO ~78 min, ODI ~22 events/hr | 1 isolated night of 4.5 h sleep |
| **Risk Classification** | **CRITICAL** (Glucose Risk: 83%) | **WARNING** (BP Risk: 71%) | **STABLE** (Risk: 12%) |
| **Clinical Finding** | **Beta-blocker masking:** Heart rate stays deceptively normal, but HRV drop and sleep debt signal impending severe next-day glucose spikes. | **Hidden Sleep Apnea:** Total sleep hours look fine on consumer trackers, but recurrent nocturnal hypoxia drives morning blood pressure surges. | **Resilience (No Alarm Fatigue):** High baseline insulin sensitivity absorbs a single bad night without triggering false alarms. |
| **What-If Solution** | Setting sleep to 7.5 h at regular bedtime drops glucose risk to **Stable** and flattens tomorrow's curve. | Toggling CPAP therapy lowers ODI by 80%, reducing morning blood pressure risk to **Stable**. | Not required; system notes the deficit but confirms stable metabolic status. |

---

## 9. Security Engineering & Safety Safeguards

1. **Model Integrity Manifest:** Pickled models are protected by SHA-256 hash checking against `models/manifest.json`. Any modified or untrusted model file is rejected on startup.
2. **Path Traversal Defense:** Static file serving verifies that file targets are strictly relative to `web/dist/`, blocking directory traversal exploits (e.g., `../../etc/passwd`).
3. **Input Validation:** Patient IDs are restricted to `^[A-Za-z0-9_-]{1,16}$`. What-If numeric inputs enforce strict bounds (`sleep_hours` between 3.0 and 10.0, finite floats only, unknown fields rejected).
4. **Rate Limiting & DoS Protection:** What-If computation endpoints are protected by an in-memory sliding-window IP rate limiter (120 requests/minute), and HTTP request bodies are capped at 4 KB.
5. **Browser Hardening:** Enforces strict Content Security Policy (`default-src 'self'`), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and `Referrer-Policy: no-referrer`.

---

## 10. Execution & Verification Guide

### Quick Start
```bash
# 1. Create and activate Python virtual environment
py -m venv .venv
.venv\Scripts\activate       # Windows PowerShell / CMD
# source .venv/bin/activate  # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the system (pipeline check + server)
python run.py

# Optional runtime flags:
# python run.py --lan        # Expose on Wi-Fi for tablet/phone access
# python run.py --port 9000  # Run on custom port
# python run.py --rebuild    # Force pipeline regeneration
# python run.py --open       # Auto-launch default web browser
```

### Access URLs
- **Web Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Running Automated Tests
```bash
# Run all 37 unit, integration, and security tests
pytest -q
```
