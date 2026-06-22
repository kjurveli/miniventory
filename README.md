# Miniventory

A terminal application for tracking your Warhammer miniatures collection.

## Features

- Manage **armies**, **units**, and **individual miniatures**
- Tag anything in your collection and filter by tags
- Track miniature paint progress (unbuilt → assembled → primed → painted → based)
- JSON file storage — no database required

## Requirements

- Python 3.10+
- [Rich](https://github.com/Textualize/rich) for terminal formatting

## Install

```bash
pip install -e .
```

## Run

```bash
miniventory
```

Or without installing:

```bash
python -m miniventory
```

Data is stored at `~/.miniventory/collection.json` by default. Override with:

```bash
miniventory --data /path/to/collection.json
```

## Data model

```
Army
 └── Unit
      └── Miniature
```

Deleting an army removes its units and miniatures. Deleting a unit removes its miniatures.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The suite includes unit tests (models, store, display) and integration tests that drive the menu flows with mocked input.

With coverage (requires `pip install coverage` or `pip install -e ".[dev]"`):

```bash
python3 -m coverage run -m unittest discover -s tests -q
python3 -m coverage report -m --include="miniventory/*"
```

## Navigation

The app uses numbered menus. Press `Ctrl+C` at any prompt to exit.

Main menu:

1. Collection overview
2. Armies — list, add, edit, delete
3. Units — list, add, edit, delete
4. Miniatures — list, add, edit, delete
5. Tags — set a global filter or browse by tag