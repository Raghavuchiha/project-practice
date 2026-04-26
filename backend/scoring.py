
# ──────────────────────────────────────────────
# scoring.py
# Step 1 : Normalize 5 metadata factors
# Step 2 : Calculate Recency Score
# Step 3 : Calculate Utility Score
# Step 4 : Assign Storage Tier
# ──────────────────────────────────────────────


def normalize(value, min_val, max_val, inverse=False):
    """
    Scales any value to 0-100 range.
    inverse=True  means lower value = higher score (e.g. days since access)
    inverse=False means higher value = higher score (e.g. access frequency)
    """
    if max_val == min_val:
        return 0

    score = (value - min_val) / (max_val - min_val) * 100

    if inverse:
        score = 100 - score

    # Keep it between 0 and 100
    score = max(0, min(100, score))

    return round(score, 2)


def calculate_recency_score(metadata):
    """
    Takes metadata dict.
    Normalizes each of the 5 factors.
    Returns weighted recency score (0 to 100).

    Weights (from paper):
      days_since_access  → 30%  (inverse: fewer days = higher score)
      access_frequency   → 25%  (direct:  more freq = higher score)
      revisit_rate       → 20%  (direct:  more revisit = higher score)
      access_decay_rate  → 15%  (inverse: slower decay = higher score)
      access_velocity    → 10%  (shift:   positive velocity = higher score)
    """

    # Normalize each factor
    norm_days     = normalize(metadata["days_since_access"],  0,    365,  inverse=True)
    norm_freq     = normalize(metadata["access_frequency"],   1,    100,  inverse=False)
    norm_revisit  = normalize(metadata["revisit_rate"],       0.0,  0.80, inverse=False)
    norm_decay    = normalize(metadata["access_decay_rate"],  3.0,  60.0, inverse=True)
    norm_velocity = normalize(metadata["access_velocity"],   -30.0, 5.0,  inverse=False)

    # Weighted sum
    recency_score = (
        0.30 * norm_days     +
        0.25 * norm_freq     +
        0.20 * norm_revisit  +
        0.15 * norm_decay    +
        0.10 * norm_velocity
    )

    return round(recency_score, 2), {
        "norm_days"     : norm_days,
        "norm_freq"     : norm_freq,
        "norm_revisit"  : norm_revisit,
        "norm_decay"    : norm_decay,
        "norm_velocity" : norm_velocity
    }


def calculate_utility_score(recency_score, ai_score, ai_label):
    """
    Real image  → utility = 0.6 x recency  (no penalty)
    AI image    → utility = 0.6 x recency  - 0.4 x (ai_score x 100)

    Weights 60/40 from paper:
    60% recency behaviour + 40% AI penalty
    """

    if ai_label == "Real":
        utility = 0.6 * recency_score
    else:
        utility = (0.6 * recency_score) - (0.4 * ai_score * 100)

    return round(utility, 2)


def assign_tier(utility_score):
    """
    Thresholds from paper:
    HOT     → utility >= 36   (premium storage)
    COLD    → utility 8 to 36 (standard storage)
    ARCHIVE → utility < 8     (cheapest storage)
    """

    if utility_score >= 36:
        return "HOT"
    elif utility_score >= 8:
        return "COLD"
    else:
        return "ARCHIVE"
