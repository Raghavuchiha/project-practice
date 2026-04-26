import random

# ──────────────────────────────────────────────
# metadata_generator.py
# Generates random metadata for any image
# Completely INDEPENDENT of AI detection result
# Ranges based on AWS S3 access pattern docs
# ──────────────────────────────────────────────

def generate_metadata(filename):
    """
    Takes an image filename.
    Returns random metadata — not based on AI or Real label.
    This keeps AI detection and metadata fully independent.
    """

    metadata = {
        "file_name"          : filename,
        "days_since_access"  : random.randint(0, 365),       # 0 = accessed today, 365 = 1 year ago
        "access_frequency"   : random.randint(1, 100),       # how many times accessed
        "revisit_rate"       : round(random.uniform(0.0, 0.80), 2),  # 0 = never revisited, 0.8 = often
        "access_decay_rate"  : round(random.uniform(3.0, 60.0), 2),  # how fast interest drops per week
        "access_velocity"    : round(random.uniform(-30.0, 5.0), 2)  # negative = declining, positive = growing
    }

    return metadata
