import numpy as np
import pandas as pd
import random
import math 

# ============================================================
# 0. CLINICIAN-CONFIGURABLE PARAMETERS (ALL EXPLICIT)
# ============================================================

CLINICIAN = {

    # --------------------------------------------------------
    # AGE DISTRIBUTION
    # checked
    # --------------------------------------------------------
    # Source:
    # - https://www.nimh.nih.gov/health/statistics/obsessive-compulsive-disorder-ocd?utm_source=chatgpt.com
    # exact: figure 1
    "age_groups": [
    ((18, 29), 1.5/4.5),
    ((30, 44), 1.4/4.5),
    ((45, 59), 1.1/4.5),
    ((60, 90), 0.5/4.5),
    ], 

    # --------------------------------------------------------
    # SEX DISTRIBUTION
    # checked
    # --------------------------------------------------------
    # https://pubmed.ncbi.nlm.nih.gov/32603559/
    # exact:  In a typical sample, women were 1.6 times more 
    # likely to experience OCD compared to men, with lifetime prevalence rates of 1.5% in women and 1.0% in men. 
    "female_probability": 1.5/2.5,  

    # --------------------------------------------------------
    # OCD SUBTYPE PREVALENCE
    # checked
    # --------------------------------------------------------
    # Source:
    # - https://pmc.ncbi.nlm.nih.gov/articles/PMC2797569/
    # Table 1: "Prevalence of each O/C in the subsample assessed for OCD"
    #
    # Exact percentages (column 1, in order appearing):
    #   Contamination:      2.9%
    #   Checking:          15.4%
    #   Ordering:           9.1%
    #   Hoarding:          14.4%   <-- EXCLUDED based on clinician feedback
    #   Sexual/religious:   2.3%
    #   Moral:              4.2%
    #   Harming:            1.7%
    #   Illness:            1.8%
    #   Other O/C:          1.1%
    #   Any of the above    28.2
    #
    # Total (excluding hoarding) = 2.9+15.4+9.1+2.3+4.2+1.7+1.8+1.1 + = 66.7
    #
    "subtype_probabilities": [
        ("contamination",     2.9/66.7),
        ("checking",         15.4/66.7),
        ("ordering",          9.1/66.7),
        ("sexual_religious",  2.3/66.7),
        ("moral",             4.2/66.7),
        ("harming",           1.7/66.7),
        ("illness",           1.8/66.7),
        ("other_oc",          1.1/66.7),
        ("any of the above",  28.2/66.7),
    ],

# --------------------------------------------------------
# SSRIs - YBOCS CHANGE FROM BASELINE
# checked
# --------------------------------------------------------
# Source:
# - https://pmc.ncbi.nlm.nih.gov/articles/PMC7025764/
# - "WMD for citalopram was ‐3.63 (95% CI ‐5.20 to ‐2.06, n=401), WMD for fluoxetine was ‐3.07 (95% CI ‐5.32 to ‐0.82, n=606), WMD for fluvoxamine was ‐3.87 (95% CI ‐5.69 to ‐2.04, n=566), WMD for paroxetine was ‐3.36 (95% CI ‐4.55 to ‐2.17, n=833) and WMD for sertraline was ‐2.45 (95% CI ‐3.54 to ‐1.35, n=691)."
# Source for ERP_SRI:
    # - https://www.sciencedirect.com/science/article/abs/pii/S0005796716301218
"ocd_treatment_ybocs": {
    "fluoxetine": {
        "mean_change": -3.07,
        "ci_95": (-5.32, -0.82),
    },
    "sertraline": {
        "mean_change": -2.45,
        "ci_95": (-3.54, -1.35),
    },
    "paroxetine": {
        "mean_change": -3.36,
        "ci_95": (-4.55, -2.17),
    },
    "fluvoxamine": {
        "mean_change": -3.87,
        "ci_95": (-5.69, -2.04),
    },
    "citalopram": {
        "mean_change": -3.63,
        "ci_95": (-5.20, -2.06),
    },
    "ERP_and_SRI": {
        "mean_change": -14.03,
        "sd": 7.11,
    },
},
    # --------------------------------------------------------
    # YBOCS 
    # checked
    # Source: Table 1: https://pmc.ncbi.nlm.nih.gov/articles/PMC3272757/
    # --------------------------------------------------------
    "baseline_ybocs": {
        "mean": 20.26,
        "sd": 8.4,
    }
}




# ============================================================
# APA ALGORITHM (SIMPLIFIED) checked!
# ============================================================
# Source: https://psychiatryonline.org/pb/assets/raw/sitewide/practice_guidelines/guidelines/ocd-1410197738287.pdf
# sOURCE:  https://med.stanford.edu/ocd/about/diagnosis.html?utm_source=chatgpt.com
#  In out experience, patients experience a 25% decrease in a Y-BOCS score as mild to moderate improvement....In controlled treatment trials, a decrease of greater than or equal to 35% is widely accepted as indicating a clinically meaningful 
# response and translates into a global improvement rating of much or very much improved
# Source for remission: https://www.psychiatrist.com/jcp/response-versus-remission-obsessive-compulsive-disorder/?utm_source=chatgpt.com
# quote-- remission rates for YBOCS < = 12:

APA_ALGORITHM = {
    "first_line": ["SSRI", "ERP_and_SRI"],
    
    "second_line": ["switch_different_SSRI"],
    
    "third_line": ["switch_different_SSRI"],
    
    "response_thresholds": {
        "clinically_meaningful": 0.35,      # ≥35% YBOCS reduction
        "moderate": 0.25,      # 25-35% reduction
        "remission_ybocs": 12  # YBOCS ≤12
    }
}


APA_ALGORITHM = {
    # Source: https://www.aafp.org/pubs/afp/issues/2015/1115/p896.html
    # Quote: "A trial of SSRI therapy should continue for 8 to 12 weeks, with at least 4 to 6 weeks at the maximal tolerable dosage."
    "first_line": {
        "options": ["SSRI", "CBT", "SSRI_plus_CBT"],
        "duration_weeks": "8-12 total (4-6 at maximal dose)",
        "note": "All three are equally valid first-line per APA"
    },
    

    # Source: https://www.aafp.org/pubs/afp/issues/2015/1115/p896.html
    # Quote1: "If there is no response to trials of at least two SSRIs, the patient should be referred to a psychiatrist. Clomipramine is an option in these patients."
    # Quote2: "Addition of an atypical antipsychotic is effective for some patients with inadequate response to SSRI therapy."
    "second_line": {
        "if_poor_response": [
            "switch_different_SSRI",  # First choice
            "switch_clomipramine",
            "augment_antipsychotic"
        ],
        "if_moderate_response": [
            "augment_antipsychotic",  # First choice for partial responders
            "add_CBT_if_not_provided"
        ]
    },
    
    # Source: https://www.aafp.org/pubs/afp/issues/2015/1115/p896.html
    "third_line": [
        "switch_different_augmenting_antipsychotic",
        "switch_different_SRI",
        "augment_clomipramine",
        "augment_glutamate_modulator"
    ],
    
    # Source: https://pubmed.ncbi.nlm.nih.gov/26833615/
    "response_thresholds": {
        "adequate": 0.35,      # ≥35% YBOCS reduction (Pallanti 2002, FDA standard)
        "moderate": 0.25,      # 25-35% reduction (Clinical trial convention)
        "remission_ybocs": 12  # YBOCS ≤12 (Consensus definition)
    }
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def weighted_choice(weighted_items):
    """
    weighted_items: list of (value, weight) tuples
    e.g. [ ((18, 29), 1.5/4.5), ((30, 44), 1.4/4.5), ... ]
    Returns ONE (value, weight) tuple sampled according to weights.
    """
    values, weights = zip(*weighted_items)
    # choose one element from weighted_items, respecting weights
    chosen = random.choices(weighted_items, weights=weights, k=1)[0]
    return chosen


def sample_age():
    (age_min, age_max), _ = weighted_choice(CLINICIAN["age_groups"])
    return int(np.random.randint(age_min, age_max + 1))

def classify_severity(ybocs_score):
    if ybocs_score <= 7: return "subclinical"
    if ybocs_score <= 15: return "mild"
    if ybocs_score <= 23: return "moderate"
    if ybocs_score <= 31: return "severe"
    return "extreme"

def assess_response(ybocs_baseline, ybocs_current):
    if ybocs_current is None:
        return {"category": "dropout", "pct_change": None, "remission": False}
    
    change = ybocs_baseline - ybocs_current
    pct_change = (change / ybocs_baseline) if ybocs_baseline > 0 else 0
    
    if pct_change >= APA_ALGORITHM["response_thresholds"]["clinically_meaningful"]:
        category = "adequate"
    elif pct_change >= APA_ALGORITHM["response_thresholds"]["moderate"]:
        category = "moderate"
    else:
        category = "poor"
    
    return {
        "category": category,
        "pct_change": pct_change,
        "remission": ybocs_current <= APA_ALGORITHM["response_thresholds"]["remission_ybocs"]
    }

def get_valid_actions(treatment_history, last_response):
    if len(treatment_history) == 0:
        return APA_ALGORITHM["first_line"]
    elif last_response == "adequate":
        return ["continue"]
    elif len(treatment_history) == 1:
        return APA_ALGORITHM["second_line"]
    else:
        return APA_ALGORITHM["third_line"]

# ============================================================
# POMDP BLACK BOX FUNCTIONS 
# NEED TO TIE IN THE ALREADY IMPLEMENTED ONES!
# ============================================================

def POMDP_INITIALIZE_BELIEF(patient_profile):
    return {"initialized": True, "patient": patient_profile}

def POMDP_GET_TRUE_STATE(patient_profile):
    return {"profile": patient_profile, "responsiveness": np.random.rand()}

def POMDP_TRANSITION(current_state, action):
    next_state = current_state.copy()
    next_state["treatment_applied"] = action
    return next_state

def POMDP_OBSERVATION(state, action):
    baseline = state["profile"]["ybocs_baseline"]
    reduction = np.random.uniform(0.2, 0.5) * baseline
    new_ybocs = max(0, baseline - reduction)
    return {"ybocs_score": new_ybocs, "dropout": np.random.rand() < 0.15}

def POMDP_REWARD(state, action, next_state, observation):
    if observation.get("dropout"):
        return -10
    baseline = state["profile"]["ybocs_baseline"]
    current = observation.get("ybocs_score", baseline)
    reduction = baseline - current
    return reduction

def POMDP_UPDATE_BELIEF(belief, action, observation):
    new_belief = belief.copy()
    new_belief["last_action"] = action
    new_belief["last_observation"] = observation
    return new_belief

def POMDP_SOLVE(belief, valid_actions):
    if "tried_actions" in belief:
        untried = [a for a in valid_actions if a not in belief["tried_actions"]]
        if untried:
            return np.random.choice(untried)
    return np.random.choice(valid_actions)

# ============================================================
# SIMULATE ONE PATIENT
# ============================================================

def simulate_one_patient(use_pomdp=True):
    patient = {}
    patient["age"] = sample_age()
    patient["gender"] = "female" if random.random() < CLINICIAN["female_probability"] else "male"
    patient["subtype"] = weighted_choice(CLINICIAN["subtype_probabilities"])
    
    baseline = float(np.random.normal(
        CLINICIAN["baseline_ybocs"]["mean"],
        CLINICIAN["baseline_ybocs"]["sd"]
    ))
    baseline = float(np.clip(baseline, 0.0, 40.0))
    patient["ybocs_baseline"] = baseline
    patient["severity"] = classify_severity(baseline)
    
    if use_pomdp:
        belief = POMDP_INITIALIZE_BELIEF(patient)
        true_state = POMDP_GET_TRUE_STATE(patient)
    else:
        belief = None
        true_state = {"profile": patient}
    
    trajectory = []
    treatment_history = []
    current_ybocs = baseline
    
    for step in range(3):
        if step == 0:
            last_response = None
        else:
            response = assess_response(
                trajectory[-1]["ybocs_before"],
                trajectory[-1]["ybocs_after"]
            )
            last_response = response["category"]
        
        valid_actions = get_valid_actions(treatment_history, last_response)
        
        if last_response == "adequate":
            break
        
        if use_pomdp:
            action = POMDP_SOLVE(belief, valid_actions)
        else:
            action = valid_actions[0]
        
        if use_pomdp:
            next_state = POMDP_TRANSITION(true_state, action)
            obs = POMDP_OBSERVATION(next_state, action)
            reward = POMDP_REWARD(true_state, action, next_state, obs)
            belief = POMDP_UPDATE_BELIEF(belief, action, obs)
            true_state = next_state
        else:
            obs = POMDP_OBSERVATION(true_state, action)
            reward = POMDP_REWARD(true_state, action, true_state, obs)
        
        trajectory.append({
            "step": step,
            "action": action,
            "ybocs_before": current_ybocs,
            "ybocs_after": obs.get("ybocs_score"),
            "dropout": obs.get("dropout", False),
            "reward": reward
        })
        
        treatment_history.append(action)
        current_ybocs = obs.get("ybocs_score", current_ybocs)
        
        if obs.get("dropout", False):
            break
    
    patient["num_treatment_steps"] = len(trajectory)
    patient["treatments_tried"] = treatment_history
    patient["final_ybocs"] = trajectory[-1]["ybocs_after"] if trajectory else None
    patient["total_reward"] = sum(t["reward"] for t in trajectory)
    
    if patient["final_ybocs"] is not None:
        final = assess_response(baseline, patient["final_ybocs"])
        patient["final_response"] = final["category"]
        patient["pct_improvement"] = final["pct_change"] * 100
        patient["achieved_remission"] = final["remission"]
    else:
        patient["final_response"] = "dropout"
        patient["pct_improvement"] = None
        patient["achieved_remission"] = False
    
    return patient

# ============================================================
# SIMULATE DATASET
# ============================================================

def simulate_dataset(n_patients=500, use_pomdp=True):
    mode = "POMDP" if use_pomdp else "STANDARD CARE"
    print(f"Simulating {n_patients} patients with {mode}...")
    
    patients = []
    for i in range(n_patients):
        if (i + 1) % 50 == 0:
            print(f"  Simulated {i + 1}/{n_patients} patients...")
        patients.append(simulate_one_patient(use_pomdp=use_pomdp))
    
    df = pd.DataFrame(patients)
    return df

# ============================================================
# MVP SUCCESS METRICS
# ============================================================

def calculate_success_metrics(df):
    """Calculate 5 key success metrics."""
    return {
        'remission_rate': (df['achieved_remission'].sum() / len(df)) * 100,
        'response_rate': ((df['final_response'] == 'adequate').sum() / len(df)) * 100,
        'any_benefit_rate': ((df['final_response'].isin(['adequate', 'moderate'])).sum() / len(df)) * 100,
        'mean_improvement': df['pct_improvement'].dropna().mean(),
        'mean_steps': df['num_treatment_steps'].mean()
    }

def compare_approaches(df_standard, df_pomdp):
    """Print comparison of key metrics."""
    std = calculate_success_metrics(df_standard)
    pomdp = calculate_success_metrics(df_pomdp)
    
    print("\n" + "=" * 70)
    print("SUCCESS METRICS COMPARISON")
    print("=" * 70)
    print(f"{'Metric':<30} {'Standard':>12} {'POMDP':>12} {'Δ':>12}")
    print("-" * 70)
    print(f"{'Remission (Y-BOCS≤12)':<30} {std['remission_rate']:>11.1f}% {pomdp['remission_rate']:>11.1f}% {pomdp['remission_rate']-std['remission_rate']:>11.1f}")
    print(f"{'Response (≥35% improve)':<30} {std['response_rate']:>11.1f}% {pomdp['response_rate']:>11.1f}% {pomdp['response_rate']-std['response_rate']:>11.1f}")
    print(f"{'Any Benefit (≥25%)':<30} {std['any_benefit_rate']:>11.1f}% {pomdp['any_benefit_rate']:>11.1f}% {pomdp['any_benefit_rate']-std['any_benefit_rate']:>11.1f}")
    print(f"{'Mean % Improvement':<30} {std['mean_improvement']:>11.1f}% {pomdp['mean_improvement']:>11.1f}% {pomdp['mean_improvement']-std['mean_improvement']:>11.1f}")
    print(f"{'Mean Treatment Steps':<30} {std['mean_steps']:>11.2f} {pomdp['mean_steps']:>11.2f} {pomdp['mean_steps']-std['mean_steps']:>11.2f}")
    
    # --- Approximate statistical significance for difference in mean % improvement ---
    imp_std = df_standard['pct_improvement'].dropna().values
    imp_pomdp = df_pomdp['pct_improvement'].dropna().values

    if len(imp_std) > 1 and len(imp_pomdp) > 1:
        n1, n2 = len(imp_std), len(imp_pomdp)
        mean_diff = imp_pomdp.mean() - imp_std.mean()

        # Sample variances with Bessel's correction
        var1 = imp_std.var(ddof=1)
        var2 = imp_pomdp.var(ddof=1)
        se_diff = np.sqrt(var1 / n1 + var2 / n2)

        if se_diff > 0:
            z = mean_diff / se_diff

            # Standard normal CDF via error function
            def norm_cdf(x):
                return 0.5 * (1.0 + math.erf(x / np.sqrt(2.0)))

            p_two_sided = 2.0 * (1.0 - norm_cdf(abs(z)))
        else:
            z = float('nan')
            p_two_sided = float('nan')

        print("\nApproximate significance test for mean % improvement (POMDP - Standard):")
        print(f"  Mean difference: {mean_diff:.2f} percentage points")
        print(f"  z ≈ {z:.2f}, two-sided p ≈ {p_two_sided:.4f}")
        if p_two_sided < 0.05:
            print("  ➜ Statistically significant at α = 0.05.")
        else:
            print("  ➜ Not statistically significant at α = 0.05.")
    else:
        print("\nNot enough data to compute a significance test.")
    
    # Quick verdict based on clinical metrics
    wins = sum([
        pomdp['remission_rate'] > std['remission_rate'],
        pomdp['response_rate'] > std['response_rate'],
        pomdp['any_benefit_rate'] > std['any_benefit_rate'],
        pomdp['mean_improvement'] > std['mean_improvement'],
        pomdp['mean_steps'] < std['mean_steps']
    ])
    
    print("\n" + "=" * 70)
    print(f"POMDP wins on {wins}/5 metrics")
    if wins >= 4:
        print("STRONG EVIDENCE of clinical value")
    elif wins >= 3:
        print("MODERATE EVIDENCE of clinical value")
    else:
        print("WEAK EVIDENCE of clinical value")
    print("=" * 70)

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    np.random.seed(42)
    random.seed(42)
    
    print("=" * 70)
    print("OCD SIMULATOR: POMDP vs STANDARD CARE")
    print("=" * 70)
    
    df_standard = simulate_dataset(n_patients=500, use_pomdp=False)
    df_pomdp = simulate_dataset(n_patients=500, use_pomdp=True)
    
    compare_approaches(df_standard, df_pomdp)
    
    df_standard.to_csv('synthetic_ocd_standard.csv', index=False)
    df_pomdp.to_csv('synthetic_ocd_pomdp.csv', index=False)
    print("\n✓ Saved: synthetic_ocd_standard.csv, synthetic_ocd_pomdp.csv")
