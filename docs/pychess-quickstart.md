# Set up a PyChess BOT

The PyChess BOT bridge connects a locally running UCI/XBoard engine to games
played on [PyChess](https://www.pychess.org/). It is based on lichess-bot,
so some source filenames and configuration keys still say `lichess`.

## Requirements

- A dedicated PyChess account **without any games played**. An existing player
  account with games cannot be converted into a BOT account.
- A PyChess API token with the `bot:play` permission. Create it from the account's
  token/settings interface. Keep it private and never post it in issues/logs.
- [uv](https://docs.astral.sh/uv/getting-started/installation/).
- A native engine executable that supports the chess variant you intend to host.

## Install and configure

```bash
git clone https://github.com/gbtami/pychess-bot.git
cd pychess-bot
uv sync --locked
cp config.yml.default config.yml
```

On Windows, copy `config.yml.default` to `config.yml` using your file manager or
PowerShell (`Copy-Item config.yml.default config.yml`). Edit the following fields
in `config.yml`, preserving the other default settings:

```yaml
token: "YOUR_PYCHESS_BOT_TOKEN"
url: "https://www.pychess.org/"
engine:
  dir: "./engines/"
  name: "YOUR_ENGINE_EXECUTABLE"
  protocol: "uci"
```

The snippet shows fields to *edit in the complete copied configuration*, not a
replacement for the full file. Put the engine executable under `engines/` or
set an appropriate absolute `engine.dir`. Set executable permissions on Unix.
Engine-specific UCI options can be configured under `engine.uci_options`; remove
options the chosen engine does not recognize. For example, Alice-Stockfish is a
specialized engine for Alice Chess; do not assume it supports the usual
`UCI_Variant` option or that every engine has the same NNUE configuration.

## Verify installation without connecting to PyChess

After `uv sync --locked`, check that the Python dependencies and BOT command load:

```bash
uv run --no-sync python lichess-bot.py --help
```

This command prints the available flags and exits **without reading your BOT
configuration, starting an engine, or contacting PyChess**. It is also exercised
in the PyChess-specific CI workflow on Python 3.10, 3.12, and 3.14. A successful
`--help` check does not establish that a particular engine works or that your
BOT token is valid.

## Convert the account and start

With your new, game-free account and its BOT token configured:

```bash
uv run python lichess-bot.py -u
```

After successful conversion, run the bot normally:

```bash
uv run python lichess-bot.py
```

The `lichess-bot.py` filename is retained deliberately for upstream merging;
it runs the PyChess fork when `url` points to PyChess. Conversion is a one-time
operation. The bot works only while this process and your engine are online.

## Troubleshooting

- **Wrong server:** Verify `url` points to PyChess, not `lichess.org`.
- **Cannot upgrade account:** Confirm it has no previously played games and
  the token has the necessary BOT permission.
- **Engine fails at startup:** Verify `engine.dir`, `engine.name`, executable
  permissions, and protocol. Remove unsupported UCI options from the sample.
- **No games:** Check the BOT account status and `challenge` filters in the
  copied configuration.

The project is based on
[lichess-bot](https://github.com/lichess-bot-devs/lichess-bot) and uses its
AGPL-3.0-or-later license. Some optional `lichess_*` configuration sections
refer to real external Lichess services; these are not PyChess server URLs.
