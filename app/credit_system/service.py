"""Credit calculation and performance tracking.
Configurable points are read from Flask config (loaded from .env)."""
from datetime import datetime
from ..models import db, User, Grievance, CreditTransaction


def award_credit(user_id: int, points: int, reason: str, grievance_id=None, flush=True):
    user = db.session.get(User, user_id)
    if not user:
        return None
    user.total_credits = (user.total_credits or 0) + points
    tx = CreditTransaction(
        user_id=user_id, grievance_id=grievance_id,
        reason=reason, points=points, balance_after=user.total_credits
    )
    db.session.add(tx)
    user.performance_level = compute_performance_level(user.total_credits)
    if flush:
        db.session.flush()
    return tx


def compute_performance_level(credits: int) -> str:
    if credits >= 500: return "Platinum"
    if credits >= 250: return "Gold"
    if credits >= 100: return "Silver"
    return "Bronze"


def apply_resolution_credits(grievance: Grievance, app_config):
    """Called when status flips to Resolved. Awards resolved + on-time + high-priority bonuses."""
    off = grievance.assigned_officer
    if not off:
        return
    awarded = []

    # Resolved base
    p = app_config.get("CREDIT_RESOLVED", 10)
    award_credit(off.id, p, f"Grievance {grievance.grievance_id} resolved", grievance_id=grievance.id, flush=False)
    awarded.append(f"Resolved: +{p}")

    # On-time bonus
    if grievance.expected_resolution_time and grievance.resolved_at \
            and grievance.resolved_at <= grievance.expected_resolution_time:
        p2 = app_config.get("CREDIT_RESOLVED_ON_TIME", 5)
        award_credit(off.id, p2, f"Grievance {grievance.grievance_id} resolved on time", grievance_id=grievance.id, flush=False)
        awarded.append(f"On-time: +{p2}")

    # High priority bonus
    if grievance.final_priority == "High":
        p3 = app_config.get("CREDIT_HIGH_PRIORITY", 10)
        award_credit(off.id, p3, f"Grievance {grievance.grievance_id} high-priority case", grievance_id=grievance.id, flush=False)
        awarded.append(f"High priority: +{p3}")

    return awarded


def officer_stats(user_id: int):
    """Return dict of performance stats for an officer."""
    gs = Grievance.query.filter_by(assigned_officer_id=user_id).all()
    total = len(gs)
    resolved = [g for g in gs if g.status == 'Resolved']
    pending = [g for g in gs if g.status not in ['Resolved', 'Rejected']]
    avg_hours = None
    if resolved:
        deltas = [(g.resolved_at - g.created_at).total_seconds() / 3600 for g in resolved if g.resolved_at and g.created_at]
        if deltas:
            avg_hours = round(sum(deltas) / len(deltas), 1)
    return {"total": total, "resolved": len(resolved), "pending": len(pending),
            "avg_resolution_hours": avg_hours}
