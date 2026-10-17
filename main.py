import argparse
import json
import logging
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk

import pytchat
import virtualbox
from supplies.BadKeyboards.BadKeyboards import BadKeyboards
from supplies.BadMouses.BadMouses import BadMouses
from supplies.ForegroundStub.ForegroundStub import ForegroundStub

LOGGER = logging.getLogger(__name__)


class Youtube2Box:
    def __init__(self, config_path="config.json", on_event=None):
        self.config_path = Path(config_path).expanduser()
        if not self.config_path.is_absolute():
            self.config_path = Path(__file__).resolve().parent / self.config_path
        with self.config_path.open("r", encoding="utf-8") as config_file:
            self.config = json.load(config_file)
        self._validate_config()
        self.on_event = on_event or (lambda message: print(message))
        self.vbox = virtualbox.VirtualBox()
        self.vm = self.vbox.find_machine(self.config["vm_name"])
        self.session = None
        self.modules = {}
        self.cmd_map = {
            command.lower(): mapping
            for command, mapping in self.config.get("Cust_plgs", {}).items()
        }
        allowed_users = self.config.get("allowed_users", [])
        self.allowed_users = {user.strip().lower() for user in allowed_users}
        self.chat_thread = None
        self.chat = None
        self.stop_event = threading.Event()
        self.action_lock = threading.RLock()
        if self.state() in ("running", "paused", "stuck"):
            self.connect_session()

    def _validate_config(self):
        if not isinstance(self.config, dict):
            raise ValueError("Configuration root must be an object")
        for key in ("vm_name", "video_id"):
            if not isinstance(self.config.get(key), str) or not self.config[key].strip():
                raise ValueError(f"Configuration field '{key}' is required")
        if not isinstance(self.config.get("Cust_plgs", {}), dict):
            raise ValueError("Configuration field 'Cust_plgs' must be an object")
        allowed_users = self.config.get("allowed_users", [])
        if not isinstance(allowed_users, list) or any(
            not isinstance(user, str) or not user.strip() for user in allowed_users
        ):
            raise ValueError("Configuration field 'allowed_users' must be an array of channel IDs")

    def emit(self, message):
        self.on_event(message)

    def state(self):
        with self.action_lock:
            return str(self.vm.state).rsplit(".", 1)[-1].lower()

    def start(self):
        with self.action_lock:
            if self.state() in ("running", "paused"):
                return "VM deja demarree"
            launch_session = virtualbox.Session()
            try:
                progress = self.vm.launch_vm_process(launch_session, "gui", "")
                progress.wait_for_completion()
            finally:
                launch_session.unlock_machine()
            self.connect_session()
            return "VM demarree"

    def connect_session(self):
        if self.session:
            return
        if self.state() not in ("running", "paused", "stuck"):
            raise RuntimeError("La VM doit etre demarree pour acceder a la console")
        self.session = self.vm.create_session()
        keyboard = self.session.console.keyboard
        mouse = self.session.console.mouse
        self.modules = {
            "BadKeyboards": BadKeyboards(keyboard, mouse),
            "BadMouses": BadMouses(keyboard, mouse),
            "ForegroundStub": ForegroundStub(keyboard, mouse),
        }

    def stop(self):
        with self.action_lock:
            if self.state() not in ("running", "paused", "stuck"):
                return "VM deja arretee"
            self.connect_session()
            progress = self.session.console.power_down()
            progress.wait_for_completion()
            self.session.unlock_machine()
            self.session = None
            self.modules = {}
            return "VM arretee"

    def pause(self):
        with self.action_lock:
            if self.state() != "running":
                raise RuntimeError("La VM doit etre en execution pour etre mise en pause")
            self.connect_session()
            self.session.console.pause()
            return "VM mise en pause"

    def resume(self):
        with self.action_lock:
            if self.state() != "paused":
                raise RuntimeError("La VM doit etre en pause pour reprendre")
            self.connect_session()
            self.session.console.resume()
            return "VM reprise"

    def reset(self):
        with self.action_lock:
            if self.state() != "running":
                raise RuntimeError("La VM doit etre en execution pour redemarrer")
            self.connect_session()
            self.session.console.reset()
            return "VM redemarree"

    def save_snapshot(self, name):
        with self.action_lock:
            snapshot_name = name.strip() or "youtube2box"
            progress = self.vm.take_snapshot(snapshot_name, "Snapshot cree depuis Youtube2Box", False)
            progress.wait_for_completion()
            return f"Snapshot cree: {snapshot_name}"

    def run_action(self, action, argument=""):
        actions = {
            "start": self.start,
            "stop": self.stop,
            "pause": self.pause,
            "resume": self.resume,
            "reset": self.reset,
            "snapshot": lambda: self.save_snapshot(argument),
            "status": lambda: f"Etat VM: {self.state()}",
        }
        if action not in actions:
            message = f"Action inconnue: {action}"
            self.emit(message)
            return message
        try:
            result = actions[action]()
            self.emit(result)
            return result
        except Exception as error:
            message = f"Erreur {action}: {error}"
            self.emit(message)
            return message

    def dispatch_chat_command(self, message):
        parts = message.strip().split(maxsplit=1)
        if not parts:
            return None
        command = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else ""
        if command == "!help":
            commands = ["!help", "!status", "!start", "!stop", "!pause", "!resume", "!reset", "!snapshot <nom>"]
            commands.extend(sorted(self.cmd_map))
            result = "Commandes: " + ", ".join(commands)
            self.emit(result)
            return result
        builtins = {
            f"!{name}": name
            for name in ("start", "stop", "pause", "resume", "reset", "snapshot", "status")
        }
        if command in builtins:
            return self.run_action(builtins[command], argument)
        if command not in self.cmd_map:
            return None
        mapping = self.cmd_map[command]
        if not isinstance(mapping, (list, tuple)) or len(mapping) != 2:
            self.emit(f"Configuration invalide pour: {command}")
            return None
        try:
            with self.action_lock:
                module_name, method_name = mapping
                if not isinstance(module_name, str) or not isinstance(method_name, str):
                    raise ValueError("les noms du plugin et de la methode doivent etre du texte")
                module = self.modules.get(module_name)
                function = getattr(module, method_name, None) if module else None
                if not callable(function):
                    raise RuntimeError("console VM indisponible ou methode inconnue")
                function(argument)
            self.emit(f"Commande executee: {command}")
        except Exception as error:
            self.emit(f"Erreur commande {command}: {error}")
        return command

    @staticmethod
    def is_public_command(message):
        parts = message.strip().split(maxsplit=1)
        return bool(parts) and parts[0].lower() in ("!help", "!status")

    def is_allowed(self, item):
        if not self.allowed_users:
            return False
        author = getattr(item, "author", None)
        channel_id = str(getattr(author, "channelId", "")).strip().lower()
        return channel_id in self.allowed_users

    def run_chat(self):
        chat = None
        try:
            chat = pytchat.create(video_id=self.config["video_id"])
            self.chat = chat
            if not self.allowed_users:
                self.emit("Commandes de controle desactivees: configurez allowed_users avec des channelId YouTube")
            self.emit(f"Chat actif pour {self.config['vm_name']}")
            while chat.is_alive() and not self.stop_event.is_set():
                for item in chat.get().sync_items():
                    if self.stop_event.is_set():
                        break
                    if self.is_allowed(item) or self.is_public_command(item.message):
                        self.dispatch_chat_command(item.message)
                    else:
                        LOGGER.warning("Commande ignoree: utilisateur non autorise")
        except Exception as error:
            LOGGER.exception("Erreur de l'ecoute YouTube")
            self.emit(f"Erreur chat: {error}")
        finally:
            if chat is not None:
                try:
                    chat.terminate()
                except Exception:
                    LOGGER.exception("Erreur lors de l'arret du chat YouTube")
            if self.chat is chat:
                self.chat = None

    def start_chat(self):
        if self.chat_thread and self.chat_thread.is_alive():
            return
        self.stop_event.clear()
        self.chat_thread = threading.Thread(target=self.run_chat, daemon=True)
        self.chat_thread.start()
        self.emit("Ecoute du chat demarree")

    def close(self):
        self.stop_event.set()
        if self.chat:
            try:
                self.chat.terminate()
            except Exception:
                LOGGER.exception("Erreur lors de l'arret du chat YouTube")
        if self.chat_thread and self.chat_thread.is_alive():
            self.chat_thread.join(timeout=5)
        with self.action_lock:
            if self.session:
                try:
                    self.session.unlock_machine()
                except Exception:
                    LOGGER.exception("Erreur lors de la fermeture de la session VM")
                finally:
                    self.session = None
                    self.modules = {}


class ControlWindow:
    def __init__(self, controller):
        self.controller = controller
        self.events = queue.Queue()
        self.shutdown_sentinel = object()
        self.closing = False
        self.root = tk.Tk()
        self.root.title("Youtube2Box - Controle VirtualBox")
        self.root.geometry("620x440")
        self.root.minsize(520, 360)
        self.status = tk.StringVar(value="Etat: inconnu")
        self._build()
        self.root.after(1000, self.refresh_state)
        self.root.after(50, self.drain_events)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)
        ttk.Label(main, text=self.controller.config["vm_name"], font=("TkDefaultFont", 17, "bold")).pack(anchor="w")
        ttk.Label(main, textvariable=self.status).pack(anchor="w", pady=(4, 14))
        power = ttk.LabelFrame(main, text="Alimentation", padding=10)
        power.pack(fill="x")
        for label, action in (("Demarrer", "start"), ("Arreter", "stop"), ("Pause", "pause"), ("Reprendre", "resume"), ("Redemarrer", "reset")):
            ttk.Button(power, text=label, command=lambda name=action: self.action(name)).pack(side="left", padx=3)
        tools = ttk.LabelFrame(main, text="Outils", padding=10)
        tools.pack(fill="x", pady=12)
        ttk.Button(tools, text="Lancer le chat", command=self.controller.start_chat).pack(side="left", padx=3)
        ttk.Button(tools, text="Snapshot", command=self.snapshot).pack(side="left", padx=3)
        self.log = tk.Text(main, height=12, state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True)
        self.controller.on_event = self.write_log

    def action(self, name):
        self.run_in_background(lambda: self.controller.run_action(name))

    def snapshot(self):
        self.run_in_background(lambda: self.controller.run_action("snapshot", "manual"))

    @staticmethod
    def run_in_background(action):
        threading.Thread(target=action, daemon=True).start()

    def refresh_state(self):
        try:
            self.status.set(f"Etat: {self.controller.state()}")
        except Exception as error:
            self.status.set(f"Etat indisponible: {error}")
        self.root.after(1000, self.refresh_state)

    def write_log(self, message):
        self.events.put(message)

    def drain_events(self):
        while True:
            try:
                message = self.events.get_nowait()
            except queue.Empty:
                break
            if message is self.shutdown_sentinel:
                self.root.destroy()
                return
            self._write_log(message)
        self.root.after(50, self.drain_events)

    def _write_log(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def close(self):
        if self.closing:
            return
        self.closing = True
        threading.Thread(target=self.shutdown, daemon=True).start()

    def shutdown(self):
        try:
            self.controller.close()
        finally:
            self.events.put(self.shutdown_sentinel)

    def run(self):
        self.root.mainloop()


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description="Controle VirtualBox via YouTube Live Chat")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--no-ui", action="store_true", help="Lancer uniquement l'ecoute du chat")
    args = parser.parse_args()
    controller = Youtube2Box(args.config)
    if args.no_ui:
        try:
            controller.run_chat()
        except KeyboardInterrupt:
            LOGGER.info("Arret demande")
        finally:
            controller.close()
    else:
        ControlWindow(controller).run()


if __name__ == "__main__":
    main()


