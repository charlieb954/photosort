# photosort

`photosort` is a simple tool to sort and organize your photos into directories
based on their metadata.

## Features

- Sort photos by date taken
- Organise photos into year directories
- Rename photos to year-month-day_counter
- Avoid having duplicate images
- Supports various image formats

## Installation

To install `photosort`, use the following command:

```bash
uv sync # OR
pip install .
```

## Example

Imagine the below tree structure, some files that shouldn't be there
(README.md), some duplicates, and different file formats.

```bash
└── test-photos
    ├── Canon_40D copy.jpg
    ├── Canon_40D.jpg
    ├── HMD_Nokia_8.3_5G.heif
    ├── Kodak_CX7530.jpg
    └── README.md
```

Running a single `photosort` command (see usage) will return these messages.

```bash
[17:38:30] INFO     Found 4 photos.
           INFO     Duplicate file found: data/test-photos/other/Canon_40D copy.jpg and data/test-photos/Canon_40D.jpg (hash:406958840ad1665ffcd1be9c29d515b9)
           WARNING  Found 1 duplicate photos. Duplicates will be ignored.
           INFO     Finished copying 3 photos.
```

`photosort` will reoganise these photos, ignoring duplicates and rename to the
below:

```bash
├── fixed
│   ├── 2008
│   │   ├── 2008-07-31_000..jpg
│   │   └── 2008-07-31_001..jpg
│   └── 2022
│       └── 2022-02-03_000..heif
└── test-photos
    ├── Canon_40D copy.jpg
    ├── Canon_40D.jpg
    ├── HMD_Nokia_8.3_5G.heif
    ├── Kodak_CX7530.jpg
    └── README.md
```

## Usage

To sort your photos, use the following command:

```bash
photosort run <src> <dest>
```

Replace `<src>` with the path to your unsorted photos and
`<dest>` with the path where you want the sorted photos to be
saved.

To see how it works, try it out with the test images in this repository

```bash
photosort run ./data/test-photos ./data/fixed
```

There is also an option to count the number of duplicates:

```bash
photosort count <src>
```
