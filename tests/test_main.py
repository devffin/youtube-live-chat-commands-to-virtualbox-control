import unittest
from threading import Event, RLock
from types import SimpleNamespace
from unittest.mock import patch

from main import Youtube2Box
from supplies.BadKeyboards.BadKeyboards import BadKeyboards
from supplies.BadMouses.BadMouses import BadMouses


def make_controller():
    controller = object.__new__(Youtube2Box)
    controller.cmd_map = {
        "!key": ["BadKeyboards", "press"],
        "!move": ["BadMouses", "move_rel"],
    }
    controller.modules = {}
    controller.allowed_users = set()
    controller.action_lock = RLock()
    controller.stop_event = Event()
    controller.chat = None
    controller.chat_thread = None
    controller.config = {"video_id": "test-video", "vm_name": "Test VM"}
    controller.vm = SimpleNamespace(state="MachineState.running")
    controller.events = []
    controller.on_event = controller.events.append
    return controller


class ControllerTests(unittest.TestCase):
    def test_empty_allowlist_rejects_control_commands(self):
        controller = make_controller()
        author = SimpleNamespace(name="viewer", channelId="UCviewer")
        self.assertFalse(controller.is_allowed(SimpleNamespace(author=author)))

    def test_allowlist_matches_channel_id_not_display_name(self):
        controller = make_controller()
        controller.allowed_users = {"uc-trusted"}
        self.assertTrue(controller.is_allowed(SimpleNamespace(
            author=SimpleNamespace(name="viewer", channelId=" UC-TRUSTED ")
        )))
        self.assertFalse(controller.is_allowed(SimpleNamespace(
            author=SimpleNamespace(name="uc-trusted", channelId="UC-other")
        )))

    def test_keyboard_failure_is_reported_as_error(self):
        class BrokenKeyboard:
            def put_keys(self, keys):
                raise RuntimeError("simulated VBox failure")

        controller = make_controller()
        controller.modules["BadKeyboards"] = BadKeyboards(BrokenKeyboard(), None)
        controller.dispatch_chat_command("!key a")
        self.assertTrue(controller.events[-1].startswith("Erreur commande !key:"))

    def test_invalid_mouse_arguments_are_reported_as_error(self):
        mouse = SimpleNamespace(put_mouse_event=lambda *args: None)
        controller = make_controller()
        controller.modules["BadMouses"] = BadMouses(None, mouse)
        controller.dispatch_chat_command("!move invalid")
        self.assertEqual(
            controller.events[-1],
            "Erreur commande !move: expected two integer coordinates",
        )

    def test_public_help_and_status_work_without_allowlist(self):
        controller = make_controller()
        self.assertIn("!snapshot <nom>", controller.dispatch_chat_command("!help"))
        self.assertEqual(controller.dispatch_chat_command("!status"), "Etat VM: running")

    def test_chat_only_dispatches_public_commands_without_allowlist(self):
        class FakeChat:
            def __init__(self):
                self.alive = True
                self.terminated = False

            def is_alive(self):
                return self.alive

            def get(self):
                self.alive = False
                items = [
                    SimpleNamespace(message="!help", author=SimpleNamespace(channelId="UCviewer")),
                    SimpleNamespace(message="!stop", author=SimpleNamespace(channelId="UCviewer")),
                ]
                return SimpleNamespace(sync_items=lambda: items)

            def terminate(self):
                self.terminated = True

        controller = make_controller()
        chat = FakeChat()
        with patch("main.pytchat.create", return_value=chat):
            controller.run_chat()
        self.assertTrue(chat.terminated)
        self.assertTrue(any(event.startswith("Commandes:") for event in controller.events))
        self.assertFalse(any(event == "VM arretee" for event in controller.events))


if __name__ == "__main__":
    unittest.main()