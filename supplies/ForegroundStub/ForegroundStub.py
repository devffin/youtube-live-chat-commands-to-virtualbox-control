class ForegroundStub:
    def __init__(self, kb, mouse):
        self.kb = kb
        self.mouse = mouse

    def focus(self, args=None):
        self.mouse.put_mouse_event(0, 0, 0, 0, 0)

    def refresh(self, args=None):
        self.focus()

    def fullscreen(self, args=None):
        self.kb.put_keys(["RCTRL", "F"])

    def keep_alive(self, args=None):
        self.kb.put_keys(["SHIFT"])

