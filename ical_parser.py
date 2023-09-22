import datetime
import time
import requests
from utils import *
import os

Settings = Settings("alex")

CALENDAR = Settings["calendar_url"]

def check_refresh(filepath, timeout=3600):
    """
    Checks the last refresh time of the calendar
    """

    if not os.path.exists(filepath):
        open(filepath, "w").close()

    with open(filepath, "r") as f:
        content = f.read(32)

    if not content.startswith("LASTREFRESH "):
        return True

    content = content.split("\n")[0].strip("LASTREFRESH ")
    last_refresh = float(content)

    if time.time() - last_refresh > timeout:
        return True

    return False


def refresh_calendar(filepath, calendar_url):
    req = requests.get(calendar_url)
    calendar_content = req.content
    calendar_content = f"LASTREFRESH {time.time()}\n".encode() + calendar_content

    with open(filepath, "wb") as f:
        f.write(calendar_content)

    return True


class Event:
    def __init__(self, tokens):
        self.start_time: datetime.datetime | None = None
        self.end_time: datetime.datetime | None = None
        self.summary: str | None = None
        self.description: str | None = None
        self.location: str | None = None
        self.status: str | None = None

        self._interprete_event(tokens)

    def _interprete_event(self, tokens):
        last_token = None

        for token in tokens:
            if token.startswith("DTSTART"):
                dt = token.split(":", 1)[1]
                self.start_time = datetime.datetime.strptime(dt, "%Y%m%dT%H%M%S")

            elif token.startswith("DTEND"):
                dt = token.split(":", 1)[1]
                self.end_time = datetime.datetime.strptime(dt, "%Y%m%dT%H%M%S")

            elif token.startswith("SUMMARY"):
                self.summary = token.split(":", 1)[1]
                last_token = "summary"

            elif token.startswith("DESCRIPTION"):
                self.description = token.split(":", 1)[1]
                last_token = "description"

            elif token.startswith("LOCATION"):
                self.location = token.split(":", 1)[1]
                last_token = "location"

            elif token.startswith("STATUS"):
                self.status = token.split(":", 1)[1]
                last_token = "status"

            elif token.startswith(" "):
                # continuation of last token
                if last_token is None:
                    raise ValueError("Invalid calendar file. Unknown token.")

                if last_token == "summary":
                    self.summary += token[1:]

                elif last_token == "description":
                    self.description += token[1:]

                elif last_token == "location":
                    self.location += token[1:]

                elif last_token == "status":
                    self.status += token[1:]

    def hash(self):
        return hash((
            self.start_time,
            self.end_time,
            self.summary,
            self.description,
            self.location,
            self.status
        ))

    def __str__(self):
        return f"Event({self.summary})"

    def __repr__(self):
        return f"<Event \"{str_max_length_cutoff(self.summary, 24)}\">"

    def length(self):
        return self.end_time - self.start_time

    def difference_with(self, other):
        other: Event
        differences = []

        if self.start_time != other.start_time:
            differences.append("start_time")

        if self.end_time != other.end_time:
            differences.append("end_time")

        if self.summary != other.summary:
            differences.append("summary")

        if self.description != other.description:
            differences.append("description")

        if self.location != other.location:
            differences.append("location")

        if self.status != other.status:
            differences.append("status")

        return differences

class Calendar:
    def __init__(self, calendar_path):
        self.path: str = calendar_path
        self.version: str
        self.prodid: str
        self.cal_name: str
        self.events: list[Event] = []

        self._load_calendar()

    def _load_calendar(self):
        with open(self.path, "r", encoding="UTF-8") as f:
            cal = f.read()

        refresh_time, *cal = cal.strip().split("\n")

        self.last_refresh = float(refresh_time.strip("LASTREFRESH "))
        self.calendar = self._interpret_calendar(cal)

    def _seperate_section(self, stream, identifyer):
        section = []

        while True:
            try:
                token = next(stream)
            except StopIteration:
                raise ValueError(f"Invalid calendar file. Missing end of section. {identifyer}")

            if token == f"BEGIN:{identifyer}":
                pass

            if token == f"END:{identifyer}":
                break

            section.append(token)

        return section

    def _handle_section(self, section_type, section):
        if section_type == "VEVENT":
            self._interpret_event(section)

    def _interpret_event(self, tokens):
        self.events.append(Event(tokens))

    def _interpret_calendar(self, tokens):
        if tokens[0] != "BEGIN:VCALENDAR" or tokens[-1] != "END:VCALENDAR":
            raise ValueError("Invalid calendar file.")

        tokens = tokens[1:-1]

        self.version = None
        self.prodid = None
        self.cal_name = None

        tokens = iter(tokens)

        while True:
            try:
                token = next(tokens)
            except StopIteration:
                break

            if token.startswith("VERSION:"):
                self.version = token.lstrip("VERSION:")
                print("Found Version: ", self.version)

            elif token.startswith("PRODID:"):
                self.prodid = token.lstrip("PRODID:")
                print("Found ProdID: ", self.prodid)

            elif token.startswith("X-WR-CALNAME:"):
                self.cal_name = token.lstrip("X-WR-CALNAME:")
                print("Found Calendar Name: ", self.cal_name)

            elif token.startswith("BEGIN:"):
                identifier = token.lstrip("BEGIN:")
                # print(f"Found section {identifier.lower()}")

                section = self._seperate_section(tokens, identifier)
                self._handle_section(identifier, section)

            else:
                print("Unknown token: ", token)

        print("Finished parsing")
        self._clean_texts()

    def _clean_texts(self):
        for event in self.events:
            event.description = event.description\
                .replace("\\n", "\n") \
                .replace("\\,", ",") \
                .strip()

            event.summary = event.summary \
                .replace("\\n", "\n") \
                .replace("\\,", ",") \
                .strip()

            event.location = event.location \
                .replace("\\n", "\n") \
                .replace("\\,", ",") \
                .strip()

    def events_on_day(self, day: datetime.date) -> list[Event]:
        for event in self.events:
            if event.start_time.date() == day:
                yield event


if __name__ == '__main__':
    fp = Settings["calendar_file"]

    if check_refresh(fp):
        print("Refreshing calendar...")
        refresh_calendar(fp, CALENDAR)
    else:
        print("Calendar up to date.")

    print("Loading calendar...")
    calendar = Calendar(fp)

    events = list(calendar.events_on_day(datetime.date.today()))

    day_start = min(events, key=lambda e: e.start_time).start_time - datetime.timedelta(minutes=30)
    day_end = max(events, key=lambda e: e.end_time).end_time + datetime.timedelta(minutes=30)
    day_length = (day_end - day_start).total_seconds() / (60 * 15)

    # 15m per line

    splices = []

    for i in range(int(day_length)):
        splices.append([
            event_i
            for event_i, e in enumerate(events)
            if e.start_time <= day_start + datetime.timedelta(minutes=15 * i) < e.end_time
        ])

    needed_width = len(max(splices, key=lambda s: len(s)))

    # add the width multiplier (un-normalised)
    splices = [
        (0, []) if not s else (needed_width / len(s), s) for s in splices
    ]
    # normalised (ensures events do not change length)
    splices = [
        (0, []) if not s[0] else
        (min(filter(lambda x: x[1] == s[1], splices), key=lambda x: x[0])[0], s[1])
        for s in splices
    ]

    STANDARD_WIDTH = 40

    rendered_events = [
        str_fixed_length(
            f"{e.summary} @ {e.location}",
            int(STANDARD_WIDTH * list(filter(lambda x: i in x[1], splices))[0][0]) - 4,
            line_nbr=int(e.length().total_seconds() / (60 * 15))
        ).split("\n") for i, e in enumerate(events)
    ]

    print("Finished visual reconstruction")

    for i, (_, es) in enumerate(splices):
        tt = (day_start + datetime.timedelta(minutes=i * 15)).time()

        if tt.minute != 0:
            rendered_time = f"  :{tt.minute!s:2}"
        else:
            rendered_time = f"{tt.hour!s:>2}:{tt.minute!s:>02}"

        print(rendered_time, end=" ")
        for e in es:
            pos = len(list(filter(lambda x: e in x[1], splices[:i])))
            rt = ["┌┐", "││"][bool(pos)]
            # rt = ["/\\", "||"][bool(pos)]

            print(f"{rt[0]} {rendered_events[e][pos]} {rt[1]}", end="")

        print()
