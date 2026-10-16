#!/usr/bin/env python3
"""Bouwt .ics-feeds (totaal + per genre) uit events.json."""
import hashlib, json, sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

GENRES = {
    "klassiek": "Klassieke muziek", "pop": "Popmuziek", "theater": "Theater & musical", "dans": "Dans",
    "opera": "Opera", "expositie": "Museumexposities", "festival": "Festivals", "film": "Film",
}
LONG = 21  # langer dan dit: aparte start- en eindmarkering

def esc(s):
    return (s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def fold(line):
    b = line.encode()
    out = []
    while len(b) > 74:
        cut = 74
        while (b[cut] & 0xC0) == 0x80:
            cut -= 1
        out.append(b[:cut].decode()); b = b[cut:]
    out.append(b.decode())
    return "\r\n ".join(out)

def vevent(uid, summary, start, end_excl, ev, stamp):
    desc = ev.get("description", "")
    if ev.get("confidence") == "estimated":
        desc += "\nLet op: datum is een inschatting op basis van eerdere edities en nog niet bevestigd."
    if ev.get("start") != ev.get("end"):
        desc += f"\nLooptijd: {fmt(ev['start'])} t/m {fmt(ev['end'])}."
    if ev.get("url"):
        desc += "\n" + ev["url"]
    loc = ", ".join(x for x in [ev.get("venue"), ev.get("city")] if x)
    lines = [
        "BEGIN:VEVENT", f"UID:{uid}@cultuurkalender", f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{start:%Y%m%d}", f"DTEND;VALUE=DATE:{end_excl:%Y%m%d}",
        f"SUMMARY:{esc(summary)}", f"DESCRIPTION:{esc(desc.strip())}",
        f"LOCATION:{esc(loc)}", f"CATEGORIES:{','.join(GENRES[g] for g in ev['genres'])}",
        "TRANSP:TRANSPARENT",
    ]
    if ev.get("url"):
        lines.append(f"URL:{ev['url']}")
    lines.append("END:VEVENT")
    return lines

MONTHS = "jan feb mrt apr mei jun jul aug sep okt nov dec".split()
def fmt(d):
    d = date.fromisoformat(d)
    return f"{d.day} {MONTHS[d.month-1]} {d.year}"

def events_for(ev, stamp):
    s, e = date.fromisoformat(ev["start"]), date.fromisoformat(ev["end"])
    base = hashlib.sha1(f"{ev['title']}|{ev.get('venue','')}".encode()).hexdigest()[:16]
    t = ev["title"] + (" (datum o.v.)" if ev.get("confidence") == "estimated" else "")
    if (e - s).days + 1 > LONG:
        return vevent(base + "-start", "▶ Start: " + t, s, s + timedelta(1), ev, stamp) + \
               vevent(base + "-eind", "■ Laatste dag: " + t, e, e + timedelta(1), ev, stamp)
    return vevent(base, t, s, e + timedelta(1), ev, stamp)

def calendar(name, evs, stamp):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Cultuurkalender//NL", "CALSCALE:GREGORIAN",
             "METHOD:PUBLISH", f"X-WR-CALNAME:{esc(name)}", "X-WR-TIMEZONE:Europe/Amsterdam",
             "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H"]
    for ev in evs:
        lines += events_for(ev, stamp)
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in lines) + "\r\n"

def main(src, out):
    evs = json.loads(Path(src).read_text())
    evs.sort(key=lambda e: (e["start"], e["title"]))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    (out / "cultuur.ics").write_text(calendar("Cultuurkalender", evs, stamp), newline="")
    for g, label in GENRES.items():
        sub = [e for e in evs if g in e["genres"]]
        (out / f"{g}.ics").write_text(calendar(f"Cultuurkalender – {label}", sub, stamp), newline="")
        print(g, len(sub))
    print("totaal", len(evs))


def write_index(src, out):
    import html
    evs = json.loads(Path(src).read_text())
    evs.sort(key=lambda e: (e["start"], e["title"]))
    safe = [{k: (html.escape(v) if isinstance(v, str) else v) for k, v in e.items()} for e in evs]
    t = (Path(__file__).parent / "index_template.html").read_text()
    t = t.replace("__GENRES__", json.dumps(GENRES, ensure_ascii=False)) \
         .replace("__EVENTS__", json.dumps(safe, ensure_ascii=False).replace("</", "<\\/")) \
         .replace("__UPDATED__", date.today().strftime("%d-%m-%Y"))
    (Path(out) / "index.html").write_text(t)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2]); write_index(sys.argv[1], sys.argv[2])
