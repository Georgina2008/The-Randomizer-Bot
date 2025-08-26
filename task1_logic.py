import random

def pick_number_from_session_v2(session: dict, user_id: int):
    """Task 1 logic: per-user unique numbers, no consecutive duplicate across users."""
    lo_hi = session["range"]
    if not lo_hi:
        return None, "no_range"
    lo, hi = lo_hi

    if user_id not in session["used"]:
        session["used"][user_id] = set()

    used_for_user = session["used"][user_id]

    available = [n for n in range(lo, hi + 1) if n not in used_for_user]
    if not available:
        return None, "depleted"

    # Prevent immediate same-number reuse across different users
    if session.get("last_user") is not None and session["last_user"] != user_id:
        available = [n for n in available if n != session.get("last_number")]
        if not available:
            return None, "depleted"

    num = random.choice(available)

    # Track per-user usage
    used_for_user.add(num)

    # Store last draw info
    session["last_number"] = num
    session["last_user"] = user_id

    return num, None
