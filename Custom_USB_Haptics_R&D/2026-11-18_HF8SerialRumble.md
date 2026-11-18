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

___

ok, this is wonderful and needs to be tested. but for now, let's go two types of
meta: buttplug of all things, why? seems completely unrelated but if the info is
out there by some reverse engineering great. the other, would this have
something to do with compatibility by the hf8 design when there is "Arduino
Shake It" and some other types documented in the simhub that also mention com1
and even the original ai-system suggestion might have had com1 in it or is it
just the remnant of the much older com port thing that has carried over to the
age of usb? and is there any other way to do it (communication) and if this is
the case then is it then closed like in any other proprietary thing like let say
psvr2 with pc which needed probing and some of it works just out of the box with
the mod for instance passthrough (but at least for the user's testing it also
had tremendous vram overhead like 3 times on their system when tested with deovr
but it might have been also due to 4500x4500 or so resolution 190% that then got
doubled in the mod hijack)

___

### 1. Why `buttplug.io` of all things?
Despite the deliberately cheeky name, **Buttplug.io / Intiface** is one of the largest open-source haptics hardware projects on GitHub. Its maintainers got tired of every vibrating gadget—controllers, wearables, VR haptics, and intimate hardware—having its own locked-down, proprietary Windows app, so they built a unified open-source hardware abstraction layer (`buttplug-rs`).

Because VR gamers, modders, and haptics tinkerers use it to sync *any* physical vibration motor to games, audio, or VR scenes, contributors routinely reverse-engineer non-adult gaming hardware and submit the protocol specs to `buttplugio/docs.buttplug.io`. That's how an 8-motor sim-racing seat pad ended up documented right next to Xbox controllers and Bluetooth toys.

---

### 2. Why is the HF8 still using a "COM port" in the USB era?
Your hunch is right on both counts: **it's a direct descendant of the old `COM1` RS-232 world, and it survives because it's the simplest possible bridge between a PC and a cheap microcontroller.**

* **Why COM ports never died:** A physical 9-pin RS-232 port is dead, **but its software model (a Virtual COM Port over USB)** is everywhere in hardware engineering. When a manufacturer puts a basic microcontroller inside a device (like an Arduino or the control box inside the HF8) to drive 8 PWM motor outputs, using a USB-to-Serial chip or USB CDC driver means:
  * Windows installs a built-in driver automatically—no custom `.sys` kernel driver signing needed.
  * The firmware inside the box only has to read simple text lines (`M0255\r`) instead of parsing complex USB HID binary descriptors.
* **Why SimHub mentions `COM` for "Arduino ShakeIt" too:** Arduino ShakeIt and the HF8 use the **same transport mechanism** (USB Virtual Serial at `115200` baud), which is why both show up as `COMx` ports in Windows Device Manager. However, they speak **different languages** over that serial wire:
  * *Arduino ShakeIt* expects SimHub's own custom Arduino firmware/protocol.
  * *HF8* (and the older Realteus ForceFeel it's based on) runs factory firmware expecting `M<0-7><0-255>\r`, which SimHub talks to via its dedicated `ForceFeel` / `NLR HF8` driver module.
* **Is there any other way to communicate with the HF8?**
  * At the **hardware level**, no. The HF8's control box only has two physical inputs: the **USB Virtual Serial port** (individual 8-motor control) and the **3.5mm audio jack** (unfiltered analog vibration across all 8 motors together). Everything else—NLR's HFS, SimHub, Intiface, or your Python script—is just talking to that same COM port.

---

### 3. "Closed" hardware: HF8 vs. PSVR2 on PC (and why your VRAM exploded)
This is a great comparison because it shows the difference between **undocumented-but-trivial** hardware vs. **actively locked-down** hardware:

* **HF8 ("lazy closed"):** NLR simply didn't publish a PDF SDK for indie programmers. There is no encryption, no cryptographic handshake, and no binary obfuscation. Five minutes of watching the USB port while dragging sliders in SimHub or HFS reveals plain ASCII text (`P\r`, `M0255\r`), and once you know those 2 commands, you have 100% native hardware control with **zero overhead**.
* **PSVR2 on PC ("actively locked" + heavy graphics pipeline):** Sony's official PC driver intentionally omitted/disabled hardware features that the headset physically supports on PS5 (eye tracking, adaptive triggers, headset haptics, passthrough overlay). Mods like `PSVR2Toolkit` had to reverse-engineer Sony's proprietary binary driver protocols and USB camera/sensor streams just to expose them to SteamVR.

**Why your PSVR2 passthrough test likely ate ~3× VRAM (especially in DeoVR at ~4500×4500 / 190%):**
Your guess is right on the money:
1. **SteamVR's base resolution is already deceptive:** Even "100%" resolution in SteamVR is ~3400×3468 *per eye* to counteract lens barrel distortion—so **190%** pushes render targets up around **~4500×4500 per eye**. A single stereo swapchain at that size (with multiple frame-in-flight buffers, mipmaps, and depth/stencil buffers) is already several gigabytes of VRAM.
2. **Passthrough hijack multiplies full-res render targets:** Normal DeoVR playback renders one stereo scene straight to the SteamVR compositor. When a passthrough/overlay mod intercepts the pipeline to blend camera feeds + chroma-key/alpha masks over DeoVR, the GPU has to hold **separate intermediate full-resolution textures/swapchains** (one for DeoVR's rendered frame, one for the passthrough/compositor overlay, plus alpha/staging buffers). If the mod allocates its buffers at SteamVR's 190% supersampled resolution rather than native panel size—or if DeoVR's own resolution scaling stacks on top—VRAM usage easily jumps **2× to 3×** and spills over into system RAM.

Thankfully, the HF8 hijack sits on the exact opposite end of the spectrum: sending `"M0255\r"` over a serial port uses effectively **0 MB of RAM/VRAM** and microseconds of CPU time.

___

ok, so how is 3.5mm audio jack conversion done if there is now freq range like
woojer, it must be closer to xbox rumble where 0-1 controls the electricity that
flows through? but what is converted into what?

___

Your intuition is spot-on: **the HF8's 3.5mm Audio Mode works almost identically to Xbox controller rumble (`0–1` controlling electricity to a motor), not like a Woojer or speaker.**

Here is the exact physical and electrical difference between the two, and what gets converted into what inside the HF8's control box.

---

### 1. Why a Woojer and an HF8 speak completely different physical languages

* **Woojer / SubPac / ButtKicker = Tactile Transducer (Speaker without a cone):**
  * Inside is a voice coil + magnet on a spring (or linear resonant actuator).
  * It takes **raw AC audio voltage** directly from an amplifier (usually low-passed below ~150–200 Hz).
  * Because AC flips positive and negative at the audio frequency, a **45 Hz** bass note literally pushes the weight back and forth **45 times per second**, and an **80 Hz** note moves it **80 times per second**. Frequency/pitch is preserved directly in the motion.

* **HF8 / Xbox Controller = ERM (Eccentric Rotating Mass) DC Motors:**
  * Inside each of the 8 pads is a regular **brushed DC motor with an off-center metal weight** on its shaft (exact same technology as an Xbox controller's rumble motors).
  * You **cannot** feed an AC audio waveform directly into a DC motor—if you flip polarity back and forth hundreds of times a second, the rotor just sits there humming and overheating.
  * An ERM motor **only understands one number: DC voltage (`0` to `1`)**, which controls **how fast the off-center weight spins**. As voltage goes up, both RPM and centrifugal shaking force go up together—completely detached from the musical pitch of the song.

---

### 2. What is converted into what in the HF8's 3.5mm Audio Mode?

When you plug a 3.5mm stereo audio cable into the HF8, the control box runs a 3-step **AC Sound Wave $\rightarrow$ Loudness Envelope $\rightarrow$ DC Motor Power** conversion (separately for Left and Right stereo channels, which is why left/right panning still works in audio mode):

```text
[ 3.5mm Stereo AC Audio ]  (Voltage swinging +/- at 20 Hz – 20,000 Hz)
          │
          ▼
[ 1. Envelope Detector ]   (Rectifies/samples |voltage| and smooths it)
          │                 Turns fast wiggling sound waves into a slow
          │                 "how loud is it right now?" number (0.0 – 1.0)
          ▼
[ 2. PWM Motor Driver ]    (Uses that 0.0 – 1.0 number as a duty cycle)
          │                 Rapidly switches the DC wall-brick power ON/OFF
          │                 (0% = 0V, 50% = half power, 100% = full power)
          ▼
[ 3. 8x ERM Motors ]       Spin faster or slower -> physical vibration
```

Notice two important consequences of that conversion:

1. **Pitch is destroyed; only "loudness" survives:**
   A loud `5,000 Hz` cymbal crash and a loud `50 Hz` kick drum both produce a high AC voltage peak $\rightarrow$ both convert to `~0.9` on the envelope detector $\rightarrow$ both spin the ERM motors at the exact same speed.
2. **Why it rumbles on upper frequencies (unlike Woojer):**
   Because the HF8 doesn't enforce a steep bass crossover filter before its envelope detector (other HF8 owners report the same thing—that audio mode *"just seems to react to any sound"* rather than isolating bass), vocals, guitars, and hi-hats all push the `0.0–1.0` envelope up and keep the motors buzzing nonstop.

---

### 3. The neat realization about your Python script

Look at what your `AudioAnimationProcessor` in `v3_32-bit_pygame_mini_audio_player.py` is already doing:
```python
D = librosa.stft(...)
self.S_magnitude = np.abs(D)
audio_envelope = np.mean(audio_stft, axis=0)
```
**Your Python script is doing the exact same "Audio $\rightarrow$ Envelope (`0–1`) $\rightarrow$ PWM (`0–255`)" conversion**, except instead of the HF8's dumb broadband analog circuit:

1. **You split the envelope into 3 clean frequency bands** (`20–200 Hz`, `200–4000 Hz`, `4000–20000 Hz`) so hi-hats don't muddy the bass motors, and you route them to separate physical zones (thighs vs. lower back vs. shoulders).
2. **You look ahead in time (`AV_SYNC_OFFSET`)**, bypassing the 117 ms WASAPI audio buffer and compensating for the physical spin-up inertia of the ERM weights—something the 3.5mm jack can *never* do because it only sees the audio *after* it leaves the soundcard.
