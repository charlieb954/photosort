# photosort

`photosort` is a simple tool to inspect, rename and organise your photos by
their metadata. It now supports three main behaviours: safe counting (no changes),
continuous incremental fixing and renaming-only workflows.

## Features

- Count mode (safe): scan a folder, compute hashes to find real duplicates,
    check extensions and report — does not create folders or move files
- Fix mode (default): incremental/continual run that processes only new
    files and leaves already-sorted folders alone (very fast for large photo
    collections)
- Force re-sort: re-check everything and re-process files when you need a
    full re-run (e.g. improved detection rules)
- Rename-only: update filenames to a consistent format while keeping files
    in their current folders (no moving)
- Avoids true duplicates using content hashes
- Supports various image formats (jpeg, heic/heif, png, etc.)

## Installation

To install `photosort`, use the following command:

```bash
uv sync # OR
pip install .
```

## Example

TODO

## Usage

`photosort` now exposes three primary commands / behaviors: count (safe), fix
(default/continual), and rename (filenames only). Use the `uv run` helper as
shown below or call the CLI directly with `photosort` depending on your
environment.

1) Just Count (Safe Mode)

This scans the folder, computes content hashes to find real duplicates,
verifies file-extensions and prints a report. It does not create folders or
copy/move files — it is read-only.

```bash
uv run photosort count --source ./test
```

2) The Continual Run (Fix — Default Behavior)

This is the normal workflow for keeping a large photo collection current.
When `--dest` is the same as `--source` (for example, your main drive),
`photosort` will skip already-sorted folders (fast) and only process new
incoming files. Example:

```bash
uv run photosort fix --source ./my_photos --dest ./my_photos
```

Scenario: You have 10,000 photos already sorted in `./my_photos/2023 Spain` and
you add a small batch of 50 new photos into `./my_photos/New_Import`.
Result: `photosort` detects that `2023 Spain` is already a sorted folder and
skips it, then finds and sorts only the 50 new photos — very fast.

3) Force Resort

If you want to re-process everything (for example after improving detection
rules), use `--force`. This will re-check and re-sort all items.

```bash
uv run photosort fix --source ./my_photos --dest ./my_photos --force
```

4) Rename-only

If you'd like to keep files where they are but tidy up their filenames
(for example `DSC001.jpg` -> `2025-01-01_DSC001.jpg`), use `rename`.

```bash
uv run photosort rename --source ./my_photos
```

5) Help

```bash
uv run photosort --help
```
