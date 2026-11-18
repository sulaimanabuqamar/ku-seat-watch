"""KU seat watcher: checks open seats in chosen sections without logging in,
and sends a phone push via ntfy.sh when any watched section has a seat."""
import os
import sys
import requests

BASE = "https://studentregistration.ku.ac.ae/StudentRegistrationSsb/ssb"
TERM = os.environ.get("TERM_CODE", "202620")  # Spring 2027
TOPIC = os.environ.get("NTFY_TOPIC", "ku-seats-fc01d7a4a2e4")

# (course combo, section) pairs to watch
WATCH = [
    ("COSC310", "01"),  # Data Structures 01, Khonji, TR 12:00 - CRN 20261
]


def get_sections(s, combo):
    s.post(f"{BASE}/classSearch/resetDataForm")
    r = s.get(
        f"{BASE}/searchResults/searchResults",
        params={
            "txt_subjectcoursecombo": combo,
            "txt_term": TERM,
            "pageOffset": 0,
            "pageMaxSize": 100,
            "sortColumn": "subjectDescription",
            "sortDirection": "asc",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("data") or []


def notify(title, msg, priority="urgent"):
    requests.post(
        f"https://ntfy.sh/{TOPIC}",
        data=msg.encode(),
        headers={"Title": title, "Priority": priority, "Tags": "rotating_light"},
        timeout=30,
    )


def main():
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (seat-watch)"
    s.get(f"{BASE}/term/termSelection?mode=search", timeout=30)
    s.post(
        f"{BASE}/term/search?mode=search",
        data={"term": TERM, "studyPath": "", "studyPathText": "",
              "startDatepicker": "", "endDatepicker": ""},
        timeout=30,
    )

    any_data = False
    for combo, sec in WATCH:
        rows = get_sections(s, combo)
        any_data = any_data or bool(rows)
        for x in rows:
            if x.get("sequenceNumber") != sec:
                continue
            seats = x.get("seatsAvailable")
            crn = x.get("courseReferenceNumber")
            print(f"{combo}-{sec} CRN {crn}: {seats} seats")
            if seats and seats > 0:
                notify(f"SEAT OPEN: {combo}-{sec}",
                       f"{combo} section {sec} (CRN {crn}) has {seats} seat(s). "
                       f"Register now: add {crn} + lab 20263.")

    if not any_data:
        print("No data returned - guest search may need login.")
        sys.exit(1)  # makes the run show as failed so you notice


if __name__ == "__main__":
    main()
