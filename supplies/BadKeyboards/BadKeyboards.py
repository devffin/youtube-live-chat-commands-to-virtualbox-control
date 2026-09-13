class BadKeyboards:
    def __init__(self, kb, mouse):
        self.kb = kb

    def press(self, args):
        keys = self._parse_keys(args)
        if not keys:
            return
        try:
            self.kb.put_keys(keys)
        except Exception as error:
            print(f"BadKeyboards error: {error}")

    def type(self, args):
        if not args:
            return
        self.kb.put_keys([self._parse_char(char) for char in args])

    def combo(self, args):
        self.press(" ".join(args.split("+")))

    def hold(self, args):
        self.press(args)

    @staticmethod
    def _parse_char(char):
        aliases = {" ": "SPACE", "\n": "ENTER", "\t": "TAB"}
        return aliases.get(char, char.upper())

    @classmethod
    def _parse_keys(cls, args):
        aliases = {
            "ctrl": "CTRL", "rctrl": "RCTRL", "alt": "ALT", "shift": "SHIFT",
            "enter": "ENTER", "esc": "ESC", "escape": "ESC", "del": "DELETE",
            "delete": "DELETE", "backspace": "BACKSPACE", "tab": "TAB", "space": "SPACE",
        }
        return [aliases.get(key.lower(), cls._parse_char(key)) for key in args.split()]

