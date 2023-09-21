import datetime
import time
import requests
from utils import *
import os

CALENDAR = Settings["calendar_url"]

def check_refresh(filepath, timeout=3600):
    """
    Checks the last refresh time of the calendar
    :return:
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
        self.calname: str
        self.events: list[Event] = []

        self._load_calendar()

    def _load_calendar(self):
        with open(self.path, "r") as f:
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
        self.calname = None

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
                self.calname = token.lstrip("X-WR-CALNAME:")
                print("Found Calendar Name: ", self.calname)

            elif token.startswith("BEGIN:"):
                identifyer = token.lstrip("BEGIN:")
                # print(f"Found section {identifyer.lower()}")

                section = self._seperate_section(tokens, identifyer)
                self._handle_section(identifyer, section)

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

    today = datetime.date.today()
    print("\n\n\nEvents tomorrow:")
    for event in calendar.events_on_day(today + datetime.timedelta(days=1)):
        print("\033[1m", event.summary, "\033[0m")

        if event.location:
            print("Location:", str_fixed_length(event.location, 60))

        if event.start_time.date() == event.end_time.date():
            print("Date:", event.start_time.date())
            print("Times:", event.start_time.time(), "-", event.end_time.time())
            print("Length:", event.length())

        else:
            print("Start:", event.start_time.date(), event.start_time.time())
            print("End:", event.end_time.date(), event.end_time.time())

        print()