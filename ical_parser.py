import requests
import time
import datetime

CALENDAR = "https://timetable.york.ac.uk/ical?650b0ed0&group=false&timetable=!MjAyMyF0ZXJtdGltZW5nX2NvdXJzZSEwMDA2LUNPSE9SVA==&eu=dHFiNTEwQHlvcmsuYWMudWs=&h=DT1kB2AiHheC3bhrhSgUpHMdfzS8pxICn_jsLPs2x0E="


def check_refresh(filepath, timeout=3600):
    """
    Checks the last refresh time of the calendar
    :return:
    """

    with open(filepath, "r") as f:
        content = f.read(32)

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


# def decode_datetime(dt):
#     year = int(dt[:4]) - 1977
#     month = int(dt[4:6])
#     day = int(dt[6:8])
#     hour = int(dt[9:11])
#     minute = int(dt[11:13])
#     second = int(dt[13:15])
#
#     return year * 31536000 + month * 2592000 + day * 86400 + hour * 3600 + minute * 60 + second


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

                # last_token += token[1:]

                if last_token == "summary":
                    self.summary += token[1:]

                elif last_token == "description":
                    self.description += token[1:]

                elif last_token == "location":
                    self.location += token[1:]

                elif last_token == "status":
                    self.status += token[1:]

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

    def events_on_day(self, day: datetime.date):
        for event in self.events:
            if event.start_time.date() == day:
                yield event


if __name__ == '__main__':
    if check_refresh("york.ics"):
        print("Refreshing calendar...")
        refresh_calendar("york.ics", CALENDAR)
    else:
        print("Calendar up to date.")

    print("Loading calendar...")
    calendar = Calendar("york.ics")

    today = datetime.date.today()
    print("\n\n\nEvents today:")
    for event in calendar.events_on_day(today):
        print("\033[1m", event.summary, "\033[0m")

        if event.location:
            print("Location:", event.location)

        if event.start_time.date() == event.end_time.date():
            print("Date:", event.start_time.date(),
                  "Time:", event.start_time.time(), "-", event.end_time.time())

        else:
            print("Start:", event.start_time.date(), event.start_time.time())
            print("End:", event.end_time.date(), event.end_time.time())

        print()