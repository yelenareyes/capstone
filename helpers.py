from datetime import date, datetime

def deadline_status(deadline_str):
    deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
    days_left = (deadline - date.today()).days

    if days_left < 0:
        return "passed"      # gray/red
    elif days_left <= 14:
        return "urgent"      # red
    elif days_left <= 45:
        return "upcoming"    # yellow
    else:
        return "later"       # green

    