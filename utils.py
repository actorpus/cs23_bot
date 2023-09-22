import json

def str_max_length_cutoff(input: str, max_length: int):
    if len(input) > max_length:
        return input[:max_length - 3] + "..."
    else:
        return input

def str_fixed_length(input: str, length: int, line_nbr: int = 0):
    # if len(input) < length:
    #     return input + (" " * (length - len(input)))

    lines = []

    while input:
        if len(input) < length:
            lines.append(input + (" " * (length - len(input))))
            break

        if " " not in input[:length]:
            lines.append(input[:length - 1] + "-")
            input = input[length:]
            continue

        cut = input[:length].rfind(" ")
        part, input = input[:cut], input[cut + 1:]

        if line_nbr and len(lines) == line_nbr - 1:
            part = part[:length - 3] + "..."
            input = ""

        lines.append(part + (" " * (length - len(part))))

    if line_nbr:
        return "\n".join(lines) + ("\n" + " " * length) * (line_nbr - len(lines))

    return "\n".join(lines)

class Settings():
    """
    settings.json:

    {
      "calendar_url": "",
      "calendar_file": ""
    }

    """

    def __init__(self, user):
        with open("settings.json", "r") as f:
            self._settings = json.load(f)[user]

    def get(self, key):
        return self._settings[key]

    def __getitem__(self, item):
        return self._settings[item]

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
    print()
    print("str_fixed_length 64 3")
    print(str_fixed_length(IPSUM_PARAGRAPH, 64, 3))
