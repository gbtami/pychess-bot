# Workflow ownership in the PyChess fork

This repository is a fork of [lichess-bot](https://github.com/lichess-bot-devs/lichess-bot).
Keep changes to inherited workflows as small as possible to simplify upstream merges.

- **`.github/workflows/pychess-bot-fork-ci.yml`** is the PyChess-owned
  lint, test, and type-check workflow on the `pychess-bot` branch.
- **`python-build.yml`, `python-test.yml`, and `mypy.yml`** target the upstream
  `master` branch. Do not enable them on `pychess-bot` without first auditing
  network calls and credentials, particularly the Lichess API token used by
  the inherited Python test workflow.
- **`versioning.yml` and `sync-wiki.yml`** already guard their jobs to the
  upstream `lichess-bot-devs/lichess-bot` repository.
- **`docker.yml`** is the inherited upstream image publisher. Its job is
  explicitly restricted to the upstream repository and a successful upstream
  `master` versioning run. It must not push images from the PyChess fork.
  The Dockerfile and upstream Docker image tags are deliberately unchanged.

No PyChess Docker image is currently published by these workflows. If PyChess
needs container releases later, add a separate PyChess-owned workflow with
its own image names, credentials, and release policy. Do not repurpose the
upstream publisher.

The PyChess CI intentionally runs without live BOT tokens and deselects the
known integration test that makes network requests. This is not a general
network sandbox: audit any new tests before assuming they are offline.
