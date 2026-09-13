class BadMouses:
    def __init__(self, kb, mouse):
        self.mouse = mouse
        self.buttons = {"left": 0x01, "right": 0x02, "middle": 0x04}

    def move_rel(self, args):
        coordinates = self._coordinates(args)
        if coordinates is None:
            return
        dx, dy = coordinates
        self.mouse.put_mouse_event(dx, dy, 0, 0, 0)

    def move_abs(self, args):
        coordinates = self._coordinates(args)
        if coordinates is None:
            return
        x, y = coordinates
        self.mouse.put_mouse_event_abs(x, y, 0, 0, 0)

    def click(self, args):
        mask = self.buttons["left"]
        self.mouse.put_mouse_event(0, 0, 0, 0, mask)
        self.mouse.put_mouse_event(0, 0, 0, 0, 0)

    def scroll(self, args):
        try:
            dz = int(args)
            self.mouse.put_mouse_event(0, 0, dz, 0, 0)
        except ValueError:
            print("BadMouses: scroll value must be an integer")

    @staticmethod
    def _coordinates(args):
        try:
            values = args.split()
            if len(values) != 2:
                raise ValueError
            return int(values[0]), int(values[1])
        except (AttributeError, ValueError):
            print("BadMouses: expected two integer coordinates")
            return None

