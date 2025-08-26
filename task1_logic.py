import random

def pick_number_from_session_v2(session: dict, guild_id: int, owner_id: int, user_id: int):
    """Task 1 logic: per-user unique numbers, no consecutive duplicate across users."""
    key = (guild_id, owner_id)

    # --- Override check ---
    if key in predefined_next and isinstance(predefined_next[key], dict):
        if user_id in predefined_next[key]:
            num = predefined_next[key].pop(user_id)
            session.setdefault("used", {}).setdefault(user_id, set()).add(num)
            session["last_number"] = num
            session["last_user"] = user_id
            return num, None
    # ----------------------

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

    used_for_user.add(num)
    session["last_number"] = num
    session["last_user"] = user_id

    return num, None
