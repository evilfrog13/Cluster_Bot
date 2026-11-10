# Cluster Bot

**Automated cluster detection and polygon marking tool for density-plot games.**

Designed for Linux (tested on Pop!_OS) to help with long data-collection sessions.  
The bot detects colored density clusters on screen, draws polygons around them, clicks **Submit**, then clicks **Continue** twice, and repeats for a set number of loops.

---

## Features

- Select the working plot area with a simple two-click selection (F1)
- Manually set the Submit / Continue button position (F3)
- Live preview of detected clusters while adjusting parameters
- Three tuning sliders:
  - **Sensitivity** – controls how many clusters are found
  - **Minimum cluster size** – ignores small noise
  - **Separation** – prevents merging nearby clusters
- Human-like mouse movement and click delays
- Configurable number of loops
- Emergency stop by moving the mouse to the top-left corner of the screen
- Saves the Submit button position between sessions

---

## Requirements

- Python 3.8 or higher
- Linux (Pop!_OS / Ubuntu recommended)
- The following Python packages:

```bash
pip3 install --user opencv-python numpy pyautogui mss pynput Pillow
```

On some systems you may also need:

```bash
sudo apt install python3-tk python3-dev
```

---

## Installation

1. Download the latest version of the script (`cluster_bot_v7.py` or newer).
2. Make it executable (optional):

```bash
chmod +x cluster_bot_v7.py
```

3. Install the required packages (see above).

---

## How to Use

1. **Start the program**
   ```bash
   python3 cluster_bot_v7.py
   ```

2. **Select the plot area (F1)**
   - Press `F1` or click the button.
   - Click the **top-left** corner of the yellow graph area.
   - Click the **bottom-right** corner of the yellow graph area.

3. **Select the Submit button (F3)**
   - Press `F3` or click the button.
   - Click once in the **middle** of the blue Submit button.
   - The same position will be used later for the Continue buttons.

4. **Tune the detection**
   - Enable **Live Preview**.
   - Move the three sliders and release the mouse.
   - Watch the preview update on the right side.
   - Aim for polygons that look similar to the ones you would draw manually.

5. **Set the number of loops** and press **F2** to start.

6. **Emergency stop**
   - Move the mouse to the **top-left corner** of the screen (PyAutoGUI failsafe).

---

## Recommended Starting Values

| Situation                    | Sensitivity | Min Size | Separation |
|-----------------------------|-------------|----------|------------|
| Few large clusters          | 0.40–0.55   | 2000–3500| 50–70      |
| Many smaller clusters       | 0.25–0.40   | 1200–2000| 40–55      |
| Mixed / pure blue clusters  | 0.30–0.45   | 1800–3000| 45–65      |

These are only starting points. Always use the Live Preview to fine-tune.

---

## Tips for Best Results

- Make the selected plot area as tight as possible around the graph (avoid UI elements).
- Higher **Separation** reduces the chance of merging two nearby clusters.
- Higher **Min Size** ignores small noise blobs.
- Lower **Sensitivity** generally finds more clusters.
- After changing a slider, release the mouse button so the Live Preview updates.
- Test the Submit button with the **TEST** button before starting a long run.

---

## File Structure

```
cluster_bot_v7.py      ← Main program
README.md              ← This file
```

---

## Known Limitations

- The detection is classical computer-vision based (no trained neural network).
- Very unusual or extremely sparse plots may need manual slider adjustment.
- The program relies on the Submit and Continue buttons staying in the same screen position.
- Works best when the game window is not minimized and the plot is fully visible.

---

## Hotkeys Summary

| Key | Action                        |
|-----|-------------------------------|
| F1  | Select plot area              |
| F2  | Start / Stop automation       |
| F3  | Select Submit button position |

---

## Disclaimer

This tool is intended for personal data-collection and testing purposes.  
Use it responsibly and in accordance with the terms of service of the game you are running.

---

## License

MIT License – feel free to modify and share.
