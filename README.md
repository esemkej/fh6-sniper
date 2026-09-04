# FH6 Sniper

A rebuilt sniper bot for Forza Horizon 6 auctions, sharing FH5 Sniper's core approach of repeatedly refreshing auction tabs, detecting available cars, and instantly buying them out using pixel detection - now with a full graphical interface to match.

---

## Features

* **Graphical Interface (GUI):** A frameless, dark-themed window for quick control over mode, infinite sniping, and custom settings, with live status messages.
* **Command-Line Interface (CLI):** The full terminal version, with the same commands and keybinds as the GUI - handy if you prefer it or the GUI misbehaves.
* **Sniping Methods:**

  * **Normal:** Standard method compatible with most FPS values.
  * **Quick:** Reduced delays for high-FPS setups.
  * **Fastest:** Fixed, minimal delays for maximum speed.
  * **Safe:** Randomized delays between inputs for stability and lower detectability; works on lower FPS.
* **Custom Mode:** Fine-tune every delay and pixel coordinate - in the GUI's dedicated setup page, or step-by-step in the terminal - with invalid values rejected before they're applied.
* **Infinite Mode:** Keep sniping automatically after every successful buyout, until manually stopped.
* **Automated Detection & Buyout:** Checks pixel colors to detect active, unsold auctions and buys out instantly, verifying success before proceeding.
* **Global Keybinds:** `Ctrl + R` toggles sniping on/off and `Ctrl + Q` force-quits, both working even while the window isn't focused.
* **Debug Mode:** Falls back automatically if the Forza window can't be found, so the bot can still be configured and tested without the game running.

---

## Usage

1. **Setup:**

   * Ensure your auction house window is open and focused on the auction house screen.
   * Lock your FPS to a stable value.

2. **Launch the script:** Run in GUI or CLI mode.

3. **Choose Sniping Method:** Normal, Quick, Fastest, Safe, or Custom (fine-tune delays and pixel positions) - via the mode dropdown in the GUI, or the `mode` command in the CLI.

4. **Start Sniping:**

   * Press Start (GUI) or use the `start [delay]` command (CLI), or trigger `Ctrl + R` at any time.
   * If Infinite sniping is enabled, the bot keeps going after each buyout; otherwise it stops after the first car.

5. **Custom Sniping:** Selecting Custom mode opens a dedicated setup page in the GUI, or walks you through each value in the terminal in CLI mode, to adjust every delay and pixel coordinate for your system.

---

## Technical Info

* Script size: ~50 KB
* EXE size: ~60 MB (packed with all dependencies using PyInstaller)

---

## What's New (v0.2)

* Added a full graphical interface alongside the CLI, matching FH5 Sniper's ease of use.
* Added a dedicated Custom mode setup page with input validation for delays and coordinates.
* Added an Infinite sniping toggle and live status toasts for mode changes and sniping state.
* Carried over the global `Ctrl + R` / `Ctrl + Q` keybinds from the CLI version.

---

## What to Expect in Future Releases

* General stability improvements as the GUI moves out of alpha.

---

# [FH5 Sniper](https://github.com/esemkej/fh6-sniper/releases/tag/v0.8)

A compact tool for automating car buyouts in Forza Horizon 5 auctions.
Designed to repeatedly refresh auction tabs, detect available cars, and instantly buy them out using pixel detection.

---

## Features

* **Graphical Interface (GUI):** A simple window-based interface for easy operation.
* **Command-Line Interface (CLI):** Run the bot directly in a terminal if the GUI behaves unexpectedly.
* **Sniping Methods:**

  * **Safe:** Randomized delays between inputs for stability and lower detectability; works on lower FPS.
  * **Normal:** Standard method from previous versions; compatible with most FPS values.
  * **Quick:** Minimal delay between inputs for high-FPS setups (144+ FPS recommended).
* **Custom Mode:** Manually adjust all pixel positions and delay timings for fine-tuning to your system or screen resolution.
* **Infinite Mode:** After successfully buying out a car, the bot continues searching and sniping automatically until manually stopped.
* **Automated Detection & Buyout:** Checks a pixel for the correct color to detect active auctions and buys out instantly; verifies success before proceeding.
* **Fully CMD-Operated Startup:** Launch the EXE, type `cli` for command-line mode or `gui` for graphical mode, and press Enter to start.

---

## Usage

1. **Setup:**

   * Ensure your auction house window is open and focused on the auction house screen.
   * Lock your FPS to a stable value.

2. **Run the EXE:**

   * Type `gui` to use the graphical interface, or `cli` to use the command-line version. Press Enter to start.

3. **Choose Sniping Method:** Safe, Normal, Quick, Custom (fine-tune delays and pixel positions), or Infinite Mode for continuous sniping.

4. **Start Sniping:**

   * Press the designated start key.
   * If infinite sniping is enabled, the bot will continue after each buyout; otherwise it stops after the first car.

5. **Custom Sniping:** Adjust all timings and pixel positions to optimize performance for your system. Default values are displayed for reference.

---

## Technical Info

* Script size: ~30 KB
* EXE size: ~60 MB (packed with all dependencies using PyInstaller)

---

## What's New (v0.8)

* Added command-line interface for users experiencing GUI issues.
* Fixed a threading bug that could crash message display.
* Other bug fixes and further improvements.

---

## What to Expect in Future Releases

* General stability improvements and minor performance updates.

---

## License

This project is licensed under the terms described in the `LICENSE` file.
