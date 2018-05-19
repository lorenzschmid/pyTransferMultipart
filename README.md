# pyTransferMultipart

This repository consists of a small daemon written in Python and its corresponding `service` configuration. The goal of the daemon is to accept multipart requests and only forward the first found JSON part of the multipart request to a given (remote) server.

The idea is to link a Plex Media Server (with a Premium subscription) and a Home Assistant instance. A Plex Media Server provides so called webhooks to quickly inform external services about its state. Unfortunately, Plex sends its updates as multipart messages while Home Assistant (via its scripts API) is expecting pure JSON messages. Now, instead of directly calling the Home Assistant API, the Plex Media Server can send its update to this daemon which then only forwards the valid JSON to the Home Assistant instance.

## Installation

1. Copy `transfer-multipart.py` to your Home Assistant home directory, e.g. `/srv/homeassistant`
2. Make it executable: `chmod +x transfer-multipart.py`
3. Create a corresponding service by copying `transfer-multipart.service` to `/etc/systemd/system/` (if your Linux distribution is `systemd` based)
4. Change `transfer-multipart.service` according to your system's structure (values to change in `<` and `>`)
5. Reload `systemd`: `sudo systemctl --system daemon-reload`
6. Enable the new service to automatically start upon boot: `sudo systemctl enable transfer-multipart`
7. Start the service `sudo systemctl start transfer-multipart`

# Command Line Interface

The Python script comes with a command line interface which works as following:

```
usage: transfer-multipart.py [-h] [-r URL] [-p PORT] [-l HOST] [--daemon]
                             [--pid-file PID_FILE] [--log-file LOG_FILE]

Transfer and strip multipart JSON messages

optional arguments:
  -h, --help            show this help message and exit
  -r URL, --url URL     Remote target URL (multiple URLs separated by comma
                        possible)
  -p PORT, --port PORT  Local port to listen on
  -l HOST, --host HOST  Local host address to listen on
  --daemon              Run script as daemon in background
  --pid-file PID_FILE   Daemon PID file path
  --log-file LOG_FILE   Daemon LOG file path
```
