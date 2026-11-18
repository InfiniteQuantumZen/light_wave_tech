2026-11-18 HF8SerialRumble

Yes—if you go **through SimHub**, your assessment is completely right:
* **Free SimHub** runs ShakeIt Motors with no feature paywall, **but** caps all hardware updates at **10 FPS (100 ms per step)**. (There is only a brief 5-minute full-speed trial.)
* At 100 ms per frame, your `0.05`s and `0.08`s drum transients get smeared or dropped completely. To get SimHub's **60 FPS (~16.7 ms)** output, you have to buy the one-off pay-what-you-want license (starting at **€8**).

**However, there is a massive plot twist:** you **do not need SimHub (or NLR's software, or Wireshark) at all.**

Community reverse-engineering (documented in the open-source `buttplug.io` project, which natively supports the pad) revealed that the **Next Level Racing HF8** does not use an encrypted USB HID protocol. It shows up in Windows as a standard **USB Serial (COM) port** and accepts plain ASCII text commands at **115,200 baud**.

That means Python can talk **directly** to the HF8 at 100+ Hz for **$0** with zero middlemen.

---

### The HF8 Direct USB Serial Protocol
According to the `buttplugio/docs.buttplug.io` protocol documentation (Issue #36):

* **Serial settings:** `115200` baud, `8` data bits, `None` parity, `1.5` stop bits, `\r` line ending.
* **Query state (`P\r`):** Returns `E<IntensityScale>,A<AudioMode>` (`0–255` dial scale, `0/1` for USB vs. 3.5mm Audio mode).
* **Set motor (`M<Motor><Intensity>\r`):** Where `Motor` is `0–7` and `Intensity` is `0–255` (e.g., `M0255\r` turns motor 0 to max, `M00\r` turns it off).
* **Motor layout:**
  * `M0` Right thigh | `M1` Left thigh
  * `M2` Right buttock | `M3` Left buttock
  * `M4` Right back | `M5` Left back
  * `M6` Right shoulder | `M7` Left shoulder

*(Note: This documented protocol applies to the standard **HF8**. If you have the newer **HF8 Pro**, its firmware may differ.)*

---

### Drop-in Python Class (`HF8SerialRumble`) — No SimHub Needed

Install `pyserial` (`pip install pyserial`), check **Windows Device Manager -> Ports (COM & LPT)** to see which `COMx` number appears when you plug in the HF8, and drop this class into `v3_32-bit_pygame_mini_audio_player.py` right next to `XboxControllerRumble`:

```python
import serial
import serial.tools.list_ports

class HF8SerialRumble:
    """
    Direct USB-Serial driver for the Next Level Racing HF8 (zero SimHub required).
    Protocol: 115200 baud, ASCII commands 'M<0-7><0-255>\\r'.
    """
    # Map your 3 frequency bands onto the 8 physical motors
    BAND_MOTORS = {
        "bass":  (0, 1, 2, 3),  # Thighs + Buttocks
        "snare": (4, 5),        # Mid/Lower Back
        "hihat": (6, 7),        # Shoulders / Upper Back
    }

    def __init__(self, port="COM3"):
        self.ser = None
        self.forces = {"bass": 0.0, "snare": 0.0, "hihat": 0.0}
        self.end_times = {"bass": 0.0, "snare": 0.0, "hihat": 0.0}
        self.last_motor_vals = [-1] * 8  # Cache to avoid resending unchanged values

        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE_POINT_FIVE,
                timeout=0.05,
                write_timeout=0.05,
            )
        except serial.SerialException:
            # Fallback if a specific Windows USB-UART driver rejects 1.5 stopbits
            try:
                self.ser = serial.Serial(
                    port=port,
                    baudrate=115200,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.05,
                    write_timeout=0.05,
                )
            except serial.SerialException as e:
                print(f"HF8 not connected on {port}: {e}")
                print("Available ports:", [p.device for p in serial.tools.list_ports.comports()])
                return

        self.check_status()

    def check_status(self):
        """Queries dial scale & USB/Audio mode using 'P\\r'."""
        if not self.ser or not self.ser.is_open:
            return
        self.ser.write(b"P\r")
        resp = self.ser.read_until(b"\r").decode("ascii", errors="ignore").strip()
        if resp:
            print(f"HF8 Status: {resp}")
            if ",A1" in resp:
                print("WARNING: HF8 is in 3.5mm Audio Mode! Hold the control button 5s for USB Mode.")

    def _apply_hardware(self):
        if not self.ser or not self.ser.is_open:
            return

        commands = []
        for band, motors in self.BAND_MOTORS.items():
            intensity = int(round(self.forces[band] * 255))
            for m in motors:
                if self.last_motor_vals[m] != intensity:
                    commands.append(f"M{m}{intensity}\r")
                    self.last_motor_vals[m] = intensity

        if commands:
            self.ser.write("".join(commands).encode("ascii"))

    def trigger(self, band, force, duration):
        if force <= 0.0 or duration <= 0.0:
            return
        self.forces[band] = max(0.0, min(1.0, force))
        self.end_times[band] = time.time() + duration

    def update(self, bass_sync=(0.0, 0.0), snare_sync=(0.0, 0.0), hihat_sync=(0.0, 0.0)):
        now = time.time()

        for band in ("bass", "snare", "hihat"):
            if self.forces[band] > 0.0 and now >= self.end_times[band]:
                self.forces[band] = 0.0

        self.trigger("bass",  *bass_sync)
        self.trigger("snare", *snare_sync)
        self.trigger("hihat", *hihat_sync)

        self._apply_hardware()

    def stop(self):
        self.forces = {"bass": 0.0, "snare": 0.0, "hihat": 0.0}
        self._apply_hardware()
        if self.ser and self.ser.is_open:
            self.ser.close()
```

---

### Summary of Your Options Now

| Route | Cost | Update Rate | Setup Effort |
| :--- | :--- | :--- | :--- |
| **Direct USB Serial (`HF8SerialRumble`)** | **$0** | **100+ Hz** (limited only by your Python `time.sleep(0.01)`) | `pip install pyserial` + find `COM` port in Device Manager |
| **SimHub (Free)** | $0 | 10 FPS (100 ms) | Too slow for sharp drum hits |
| **SimHub (Licensed)** | ~€8 once | 60 FPS (16.7 ms) | Useful if you also want SimHub's GUI sliders or game telemetry |

*(Just make sure NLR's HFS software and SimHub are closed when running `HF8SerialRumble`, because only one program can open a Windows COM port at a time.)*
