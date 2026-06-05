# HistoCRF-GUI

A lightweight whole-slide image (SVS) viewer built with PyQt6 and OpenSlide for the HistoCRF algorithm.

The viewer loads Aperio `.svs` files, displays image regions on demand using the slide pyramid, supports smooth zooming and panning, and includes a minimap navigator showing the current viewport position.

## Requirements

- Python 3.10.11
- OpenSlide binaries 4.0.0.13

Python packages:

```
pip install PyQt6 openslide-python pillow
```

## OpenSlide Installation

Download the [OpenSlide Windows binaries](https://github.com/openslide/openslide-bin/releases/tag/v4.0.0.13) (version 4.0.0.13) and update the `OPENSLIDE_PATH` variable in the script to point to the `bin` directory:

```
OPENSLIDE_PATH = r"path/to/openslide-bin-4.0.0.13/bin"
```


## Running

```
python HistoCRF_GUI.py
```

Click **Open SVS** and select a `.svs` file.

## Controls

|Action|Control|
|---|---|
|Zoom in/out|Mouse wheel|
|Pan|Left mouse drag|
|Jump using minimap|Click or drag in minimap|
|Save coordinate|Right-click|

## Notes

This project is intended as viewer for the [HistoCRF](https://github.com/tgodelaine/HistoCRF) algorithm.
