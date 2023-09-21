import json

def str_max_length_cutoff(input: str, max_length: int):
    if len(input) > max_length:
        return input[:max_length - 3] + "..."
    else:
        return input

def str_fixed_length(input: str, length: int):
    if len(input) < length:
        return input + (" " * (length - len(input)))

    lines = []

    while input:
        if len(input) < length:
            lines.append(input + (" " * (length - len(input))))
            input = ""
            continue

        if " " not in input[:length]:
            lines.append(input[:length - 1] + "-")
            input = input[length:]
            continue

        cut = input[:length].rfind(" ")
        part, input = input[:cut], input[cut + 1:]

        lines.append(part + (" " * (length - len(part))))

    return "\n".join(lines)

class Settings():
    """
    settings.json:

    {
      "calendar_url": "",
      "calendar_file": ""
    }

    """

    def __init__(self):
        with open("settings.json", "r") as f:
            self._settings = json.load(f)

    def get(self, key):
        return self._settings[key]

    def __getitem__(self, item):
        return self._settings[item]

Settings = Settings()


IPSUM_PARAGRAPH = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut " \
                  "labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris " \
                  "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate " \
                  "velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non " \
                  "proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
IPSUM_SHORT = "Lorem ipsum dolor sit amet, consectetur adipiscing elit"

if __name__ == '__main__':
    print("original")
    print(IPSUM_PARAGRAPH)
    print()
    print("str_max_length_cutoff 64")
    print(str_max_length_cutoff(IPSUM_PARAGRAPH, 64))
    print()
    print("str_fixed_length 64")
    print(str_fixed_length(IPSUM_PARAGRAPH, 64))
