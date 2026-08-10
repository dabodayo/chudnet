#!/usr/bin/env python3
"""Convert shifts.json into an .ics file importable into Apple Calendar."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

INPUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("shifts.json")
OUTPUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("schedule.ics")


def fold(line: str) -> str:
    """RFC 5545 line folding at 75 octets."""
    out, rest = line[:75], line[75:]
    while rest:
        out += "\r\n " + rest[:74]
        rest = rest[74:]
    return out


def main() -> None:
    data = json.loads(INPUT.read_text())
    tz = ZoneInfo(data["timezone"])
    now_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//chudnet//Schedule Export//EN",
        "CALSCALE:GREGORIAN",
        fold(f"X-WR-CALNAME:{data.get('calendar_name', 'Job Schedule')}"),
        f"X-WR-TIMEZONE:{data['timezone']}",
        "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
        "X-PUBLISHED-TTL:PT1H",
    ]

    count = 0
    for item in data["shifts"] + data.get("events", []):
        date = item["date"]
        location = item.get("location", "")
        start = datetime.strptime(f"{date} {item['start']}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
        end = datetime.strptime(f"{date} {item['end']}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
        if end <= start:
            end = end.replace(day=end.day + 1)  # overnight shift wraps to next day

        start_utc = start.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        end_utc = end.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        # Stable per-item UID (date+start+location) so refreshing the
        # subscription updates events in place instead of duplicating them,
        # while still allowing multiple entries on the same date.
        uid = hashlib.sha1(f"{date}|{item['start']}|{location}".encode()).hexdigest()

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}@chudnet",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART:{start_utc}",
            f"DTEND:{end_utc}",
            fold(f"SUMMARY:{item['label']}"),
        ]
        if location:
            lines.append(fold(f"LOCATION:{location}"))
        lines.append("END:VEVENT")
        count += 1

    lines.append("END:VCALENDAR")
    OUTPUT.write_text("\r\n".join(lines) + "\r\n")
    print(f"Wrote {count} events to {OUTPUT}")


if __name__ == "__main__":
    main()
