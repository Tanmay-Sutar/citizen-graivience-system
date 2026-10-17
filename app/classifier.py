"""
ML / NLP classifier for the Citizen Grievance System.

Uses scikit-learn models trained by train_model.py:
  - TF-IDF + Logistic Regression for CATEGORY (Water / Road / Electricity)
  - TF-IDF + Logistic Regression for PRIORITY (High / Medium / Low)

Models are loaded from app/ml_models/*.joblib via joblib.

If the trained models are NOT found (e.g. train_model.py was never run),
this module falls back to a deterministic keyword-based rule matcher so the
app still works out of the box. Run `python train_model.py` to enable ML.

Public API:
  - run_predictions(complaint_text, citizen_category, citizen_priority)
      Returns dict with category, category_confidence, priority,
      priority_confidence, and top_terms (explainability).
"""
import os
import re
import logging

log = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml_models")

# ------------------------------------------------------------------
# Lazy-load ML models (loaded once on first use)
# ------------------------------------------------------------------
_ml_cache = {"loaded": False, "ok": False}


def _load_ml():
    """Load joblib models once. Returns True if ML is available."""
    if _ml_cache["loaded"]:
        return _ml_cache["ok"]
    _ml_cache["loaded"] = True
    try:
        import joblib
        cat_model = joblib.load(os.path.join(MODEL_DIR, "category_model.joblib"))
        cat_vec = joblib.load(os.path.join(MODEL_DIR, "category_vectorizer.joblib"))
        pri_model = joblib.load(os.path.join(MODEL_DIR, "priority_model.joblib"))
        pri_vec = joblib.load(os.path.join(MODEL_DIR, "priority_vectorizer.joblib"))
        encoders = joblib.load(os.path.join(MODEL_DIR, "label_encoders.joblib"))
        _ml_cache["cat_model"] = cat_model
        _ml_cache["cat_vec"] = cat_vec
        _ml_cache["pri_model"] = pri_model
        _ml_cache["pri_vec"] = pri_vec
        _ml_cache["encoders"] = encoders
        _ml_cache["ok"] = True
        log.info("ML models loaded successfully from %s", MODEL_DIR)
        return True
    except Exception as exc:
        log.warning("Could not load ML models (%s). Falling back to rule-based classifier.", exc)
        _ml_cache["ok"] = False
        return False


# ------------------------------------------------------------------
# Text preprocessing (must match train_model.py)
# ------------------------------------------------------------------
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    try:
        STOPWORDS = set(stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords", quiet=True)
        STOPWORDS = set(stopwords.words("english"))
    try:
        lemmatizer = WordNetLemmatizer()
        nltk.download("wordnet", quiet=True)
        nltk.download("omw-1.4", quiet=True)
    except Exception:
        lemmatizer = None
except Exception:
    STOPWORDS = set("""a an the and or but if then of to in on at for with by from as is are was were
    be been being have has had do does did will would shall should may might can could this that these
    those it its i you he she we they me him her us them my your his our their what which who whom
    not no so such only own same than too very just about above after again against all am any because
    before between both during each few more most other some into through under until up down out off
    over here there when where why how""".split())
    lemmatizer = None


def preprocess(text: str) -> str:
    """Lowercase, remove punctuation & stopwords, optional lemmatization."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [t for t in text.split() if t and t not in STOPWORDS]
    if lemmatizer is not None:
        tokens = [lemmatizer.lemmatize(t) for t in tokens]
    return " ".join(tokens)


# ------------------------------------------------------------------
# Rule-based fallback keyword dictionaries
# ------------------------------------------------------------------
WATER_KEYWORDS = [
    "water", "pipe", "tap", "leak", "leaking", "flood", "flooded", "drain", "sewage", "sewer",
    "supply", "tanker", "shortage", "tank", "overflow", "contaminated", "contamination",
    "pressure", "drinking", "hydrant", "drainage", "sump", "pump", "borewell", "chlorine",
    "smell", "brown water", "toilet", "flush", "washroom", "bathroom"
]
ROAD_KEYWORDS = [
    "road", "pothole", "potholes", "street", "highway", "lane", "footpath", "sidewalk", "curb",
    "pavement", "asphalt", "resurface", "crack", "sinkhole", "cave", "caved", "bridge", "divider",
    "median", "crosswalk", "zebra", "sign", "signage", "signal", "speed", "breaker", "hump",
    "manhole", "debris", "landslide", "bus stop", "bench", "bus stand", "roadside", "intersection",
    "junction", "roundabout", "parking", "dust", "shoulder", "reflector", "marking", "pot hole"
]
ELECTRICITY_KEYWORDS = [
    "electric", "electricity", "power", "light", "street light", "streetlight", "wire", "cable",
    "transformer", "meter", "bill", "substation", "shock", "spark", "sparking", "outage", "blackout",
    "voltage", "fluctuation", "bulb", "pole", "lamppost", "lamp", "lighting", "socket", "plug",
    "switch", "generator", "ups", "inverter", "live wire", "fire", "burning", "smoke", "catching",
    "charging", "solar", "grid", "powercut", "power cut", "power outage", "electrical", "wiring"
]
HIGH_KEYWORDS = [
    "dangerous", "danger", "emergency", "urgent", "critical", "severe", "major", "extreme",
    "accident", "fire", "explosion", "burst", "collapsed", "collapse", "fallen", "falling",
    "live wire", "exposed", "electrocution", "death", "killed", "hospital", "injured", "bleeding",
    "massive", "catastrophic", "health risk", "risk", "hazard", "hazardous", "toxic", "immediate",
    "sinkhole", "blocked", "no water", "no supply", "3 days", "several days", "school zone",
    "children", "patient", "contaminated", "raw sewage", "sagging", "leaning", "blackout",
    "cave in", "sink", "huge", "entire", "whole", "many", "frequent"
]
MEDIUM_KEYWORDS = [
    "issue", "problem", "not working", "broken", "damaged", "faded", "low", "incorrect", "wrong",
    "missing", "incomplete", "failing", "worn", "rusted", "clogged", "slow", "late", "irregular",
    "unusual", "noise", "hum", "vibration", "dusty", "need repair", "needs replacement", "high bill",
    "billing", "fluctuates", "several", "multiple"
]
LOW_KEYWORDS = [
    "minor", "small", "little", "slight", "adjustment", "simple", "cosmetic", "easy", "tile loose",
    "plate faded", "cover loose", "timer", "battery", "remote", "dim", "single", "one", "slightly",
    "weed", "graffiti", "chip", "crack small", "minor leak", "tighten", "reattach"
]


def _rule_score(text, keywords):
    from collections import Counter
    counts = Counter(text.split())
    score = 0.0
    for kw in keywords:
        parts = kw.split()
        if len(parts) == 1:
            score += counts.get(parts[0], 0)
        elif all(p in text for p in parts):
            score += 2.0
    return score


def _rule_predict_category(text):
    sw = _rule_score(text, WATER_KEYWORDS)
    sr = _rule_score(text, ROAD_KEYWORDS)
    se = _rule_score(text, ELECTRICITY_KEYWORDS)
    scores = {"Water": sw, "Road": sr, "Electricity": se}
    total = sum(scores.values())
    if total == 0:
        return None, 0.0
    best = max(scores, key=scores.get)
    conf = scores[best] / total
    if (scores[best] - sorted(scores.values())[-2]) >= 3:
        conf = min(1.0, conf + 0.1)
    return best, round(conf, 3)


def _rule_predict_priority(text):
    sh = _rule_score(text, HIGH_KEYWORDS)
    sm = _rule_score(text, MEDIUM_KEYWORDS)
    sl = _rule_score(text, LOW_KEYWORDS)
    scores = {"High": sh, "Medium": sm, "Low": sl}
    total = sum(scores.values())
    if total == 0:
        return None, 0.0
    best = max(scores, key=scores.get)
    conf = scores[best] / total
    if (scores[best] - sorted(scores.values())[-2]) >= 3:
        conf = min(1.0, conf + 0.1)
    return best, round(conf, 3)


def _top_terms_for_text(model, vectorizer, text_clean, top_n=5):
    """Return the top TF-IDF terms that most influenced the predicted class (explainability)."""
    try:
        vec = vectorizer.transform([text_clean])
        feature_names = vectorizer.get_feature_names_out()
        # Get the predicted class and its coefficients
        pred = model.predict(vec)[0]
        classes = list(model.classes_)
        if pred in classes:
            idx = classes.index(pred)
            coefs = model.coef_[idx] if len(classes) > 2 else model.coef_[0]
            # Multiply TF-IDF vector by coefficients to get contribution
            contribution = vec.toarray()[0] * coefs
            top_indices = contribution.argsort()[-top_n:][::-1]
            return [feature_names[i] for i in top_indices if contribution[i] > 0][:top_n]
    except Exception:
        pass
    return []


# ------------------------------------------------------------------
# Public prediction functions
# ------------------------------------------------------------------
def predict_category(text: str):
    """Return (category_label, confidence 0..1). Uses ML if available, else rules."""
    cleaned = preprocess(text)
    if _load_ml():
        try:
            vec = _ml_cache["cat_vec"].transform([cleaned])
            probs = _ml_cache["cat_model"].predict_proba(vec)[0]
            classes = list(_ml_cache["cat_model"].classes_)
            best_idx = int(probs.argmax())
            return classes[best_idx], round(float(probs[best_idx]), 3)
        except Exception as exc:
            log.warning("ML category prediction failed (%s), using rules.", exc)
    return _rule_predict_category(cleaned)


def predict_priority(text: str):
    """Return (priority_label, confidence 0..1). Uses ML if available, else rules."""
    cleaned = preprocess(text)
    if _load_ml():
        try:
            vec = _ml_cache["pri_vec"].transform([cleaned])
            probs = _ml_cache["pri_model"].predict_proba(vec)[0]
            classes = list(_ml_cache["pri_model"].classes_)
            best_idx = int(probs.argmax())
            return classes[best_idx], round(float(probs[best_idx]), 3)
        except Exception as exc:
            log.warning("ML priority prediction failed (%s), using rules.", exc)
    return _rule_predict_priority(cleaned)


def run_predictions(complaint_text: str, citizen_category: str = None, citizen_priority: str = None):
    """
    Main entry point used by grievance submission.
    Returns:
      {
        "category": str, "category_confidence": float,
        "priority": str,  "priority_confidence": float,
        "top_terms": list[str]   (top TF-IDF words influencing the prediction)
      }
    If ML confidence is very low (< 0.30), fall back to the citizen's suggestion.
    """
    cat, cat_conf = predict_category(complaint_text)
    pri, pri_conf = predict_priority(complaint_text)

    cleaned = preprocess(complaint_text)
    top_terms = []
    if _load_ml():
        top_terms = _top_terms_for_text(_ml_cache["cat_model"], _ml_cache["cat_vec"], cleaned)

    # Low confidence -> use citizen's suggestion as a fallback
    if cat is None or cat_conf < 0.30:
        cat = citizen_category
        cat_conf = 0.33
    if pri is None or pri_conf < 0.30:
        pri = citizen_priority
        pri_conf = 0.33

    return {
        "category": cat,
        "category_confidence": round(cat_conf, 3),
        "priority": pri,
        "priority_confidence": round(pri_conf, 3),
        "top_terms": top_terms,
    }
