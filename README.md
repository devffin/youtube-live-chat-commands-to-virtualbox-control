# YouTube Live Chat → VirtualBox Controller

A small bridge that lets you control VirtualBox VMs using commands sent in a YouTube live chat. This project is in an alpha state — use with caution. If you improve stability or add features, contributions and pull requests are welcome.

## Status

Alpha — actively being reworked. Not production-ready. Use on test machines and review code before running with elevated privileges.

## Features (example)

- Listen to a YouTube live chat stream
- Parse chat messages for predefined commands
- Map chat commands to VirtualBox actions (start, stop, pause, snapshot, send keyboard/mouse events)
- Basic access control via allowed user list or command tokens

> The exact supported commands and configuration depend on the implementation files in the repo. The README below gives a generic setup and usage guide you can adapt.

## Requirements

- VirtualBox installed and `VBoxManage` available on PATH
- Python 3.8+ (or the language/runtime used by the project)
- Google API credentials (OAuth 2.0 client or API key with YouTube Data API / YouTube Live Streaming access)
- Network access to YouTube live chat
- (Optional) A dedicated low-privilege account to run the controller

## Security notes

- Running remote-controlled VM actions is dangerous. Restrict access:
  - Limit which YouTube accounts can send commands (whitelist)
  - Use command tokens or moderator-only commands
  - Run controller with least privilege required
  - Test carefully on non-production systems

## Quick start (Python example)

1. Clone the repo:
   git clone https://github.com/devffin/youtube-live-chat-commands-to-virtualbox-control.git
2. Create a virtual environment and install dependencies:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
3. Obtain Google API credentials:
   - Create OAuth 2.0 client credentials in Google Cloud Console
   - Enable the YouTube Data API for your project
   - Save `client_secrets.json` to the project directory (or follow the repo-specific config)
4. Configure the controller:
   - Create a config file (example below) or set environment variables
5. Run the controller:
   python main.py --config config.yaml

Adjust commands and script name to match the repository implementation.

## Example configuration (yaml)

```yaml
youtube:
  live_chat_id: YOUR_LIVE_CHAT_ID_OR_STREAM_ID
  credentials_file: client_secrets.json
  allowed_users:
    - your_channel_name
    - trusted_moderator

virtualbox:
  vm_name: "Test VM"
  vboxmanage_path: "VBoxManage" # optional if on PATH

commands:
  start: "startvm"
  stop: "controlvm acpipowerbutton"
  pause: "controlvm pause"
  resume: "controlvm resume"
  snapshot: "snapshot take {name}"
```

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
