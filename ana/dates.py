from datetime import date, datetime
from typing import Optional, Tuple


def next_occurrence(day: int, month: Optional[int] = None, year: Optional[int] = None) -> date:
    """
    Return the next future (or today) occurrence of the given date components.

    - Only day given       → next occurrence of that day-of-month (any month)
    - Day + month given    → next occurrence of day/month (this year or next)
    - Day + month + year   → exact date (validated)
    """
    today = date.today()

    if year is not None:
        # Exact date
        return date(year, month, day)

    if month is not None:
        # Next occurrence of day/month
        candidate = date(today.year, month, day)
        if candidate < today:
            candidate = date(today.year + 1, month, day)
        return candidate

    # Only day given — find the next month where this day exists and is >= today
    y, m = today.year, today.month
    for _ in range(13):  # at most 13 months ahead
        try:
            candidate = date(y, m, day)
            if candidate >= today:
                return candidate
        except ValueError:
            pass  # day doesn't exist in this month (e.g. 31 in April)
        m += 1
        if m > 12:
            m = 1
            y += 1

    raise ValueError(f"Could not find a valid next occurrence for day {day}")


def parse_date_args(args: list[str]) -> Tuple[date, Optional[str], str]:
    """
    Parse a flexible list of string args into (date, time_str_or_None, description).

    Accepted patterns (args after the command name):
      day "text"
      day HH:MM "text"
      day month "text"
      day month HH:MM "text"
      day month year "text"
      day month year HH:MM "text"

    Returns:
      (resolved_date, time_str_or_None, description)
    """
    if len(args) < 1:
        raise ValueError("Need at least a description.")

    def is_time(s: str) -> bool:
        parts = s.split(":")
        return (
            len(parts) == 2
            and parts[0].isdigit()
            and parts[1].isdigit()
            and 0 <= int(parts[0]) <= 23
            and 0 <= int(parts[1]) <= 59
        )

    def is_int(s: str) -> bool:
        try:
            int(s)
            return True
        except ValueError:
            return False

    # The description is always the last arg
    description = args[-1]
    rest = args[:-1]  # everything before the description

    time_str: Optional[str] = None

    # Check if last of rest is a time
    if rest and is_time(rest[-1]):
        time_str = rest[-1]
        rest = rest[:-1]

    # Now rest is: [day] or [day, month] or [day, month, year]
    if not rest:
        # No date given — use today
        return date.today(), time_str, description

    if not all(is_int(x) for x in rest):
        raise ValueError(f"Expected numeric date components, got: {rest}")

    nums = [int(x) for x in rest]

    if len(nums) == 1:
        resolved = next_occurrence(nums[0])
    elif len(nums) == 2:
        resolved = next_occurrence(nums[0], nums[1])
    elif len(nums) == 3:
        resolved = next_occurrence(nums[0], nums[1], nums[2])
    else:
        raise ValueError("Too many date components. Use: day [month [year]] [HH:MM] \"text\"")

    return resolved, time_str, description


def format_event_date(day: int, month: int, year: int, time_str: Optional[str]) -> str:
    if time_str:
        return f"{day:02d}/{month:02d}/{year} {time_str}"
    return f"{day:02d}/{month:02d}/{year}"
