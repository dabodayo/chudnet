# chudnet

Generates an Apple Calendar-importable `.ics` file from a work shift schedule.

## Usage

1. Edit `shifts.json` with your shifts for the week (24-hour `HH:MM` times, in the
   listed `timezone`).
2. Run:

   ```
   python3 generate_ics.py
   ```

3. This writes `schedule.ics`. Open it on your iPhone/Mac (or AirDrop it to
   yourself) and tap through the import prompt to add the events to Apple
   Calendar.
