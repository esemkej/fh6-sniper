# FH6 Sniper
Alpha version of the new and improved sniper bot for Forza Horizon 6 auctions.
Works largely the same but only in CLI mode for now
More info in the help command print

---

# FH5 Sniper

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
   * Lock your FPS to a stable value and toggle fullscreen off if using a non-16:9 resolution.

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
