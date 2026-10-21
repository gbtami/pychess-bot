# PyChess BOT

Run your own chess-variant engine as a BOT opponent on [PyChess](https://www.pychess.org/).
This project is a PyChess-specific fork of [lichess-bot](https://github.com/lichess-bot-devs/lichess-bot).
It retains upstream engine handling and much of its internal terminology to make
future upstream merges easier.

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and obtain
an executable UCI or XBoard chess engine supported by your chosen variant.

```bash
git clone https://github.com/gbtami/pychess-bot.git
cd pychess-bot
uv sync
cp config.yml.default config.yml
```

Edit `config.yml`: set `url: "https://www.pychess.org/"`, enter the PyChess
BOT token, and configure `engine.dir` and `engine.name` to point to your engine.
Then run:

```bash
uv run python lichess-bot.py -u   # Convert the new account to a BOT account (once)
uv run python lichess-bot.py      # Start accepting challenges
```

**Important:** Create a dedicated PyChess account with **no previously played
games** before upgrading it to BOT status. Treat your API token as a password;
never commit `config.yml`. Conversion is only needed once. Your engine and this
process must remain running to play games.

See [the PyChess setup guide](docs/pychess-quickstart.md) for token scopes,
engine configuration, and troubleshooting. `uv` replaces manual virtualenv and
`pip install -r requirements.txt` steps; the legacy entrypoint remains for
upstream compatibility.

## Origin and license

This is a fork of the [lichess-bot project](https://github.com/lichess-bot-devs/lichess-bot),
which originated with the Lichess community. We gratefully retain upstream
attribution, the original project history, and its AGPL-3.0-or-later license.
See [LICENSE](LICENSE) and [upstream documentation](https://github.com/lichess-bot-devs/lichess-bot/wiki)
for general engine features; **upstream Lichess account and token instructions do
not apply to PyChess**.
