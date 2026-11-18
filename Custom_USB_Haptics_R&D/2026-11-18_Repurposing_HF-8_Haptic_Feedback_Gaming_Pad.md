2026-11-18: Repurposing HF-8 Haptic Feedback Gaming Pad

just played a bit forza horizn 5, checked the settings and couldn find anything
relating to the following: how is the simhub supposed to work when there is no
settings anywhere to be seen? and how is this telemetry data even working?
through external files (which seem oddly slow) or some communication protocol?
and how is this Next Level Racing HF-8 Haptic Feedback Gaming Pad supposed to
work with the thing (simhub) based on the previous since it seems to be able to
work without next level racing own software? and how is their software then
supposed to work with it? and furthermore, how is the simhub be able to connect
to the this device and is it some form of proprietary hardware solution that is
based on custom dashboards?

___

Here is how all the pieces fit together—from Forza Horizon 5’s hidden menu all the way down to the USB signals hitting the motors in your seat.

---

### 1. Where are the settings in Forza Horizon 5?
Forza Horizon 5 *does* have telemetry settings, they are just buried at the very bottom of a menu you wouldn't normally expect:

1. Open **Settings** -> **HUD and Gameplay**.
2. Scroll **all the way down to the bottom**.
3. You will see three options (turned off by default):
   * **Data Out:** Set to **On**.
   * **Data Out IP Address:** Set to `127.0.0.1` (if SimHub is on the same PC).
   * **Data Out IP Port:** Set this to match the exact port shown in SimHub under **Games -> Forza Horizon 5** (for example, `5607` or whatever SimHub is listening on).

**Two common FH5 gotchas:**
* **No data in menus:** FH5 stops transmitting telemetry while you are in menus, paused, or in photo mode—you have to actually be out driving a car for SimHub to show data.
* **Microsoft Store / Xbox App version:** If you didn't buy FH5 on Steam, Windows runs Store games inside an "AppContainer" security sandbox that blocks `127.0.0.1` local connections by default. SimHub usually offers to apply a Windows loopback exemption (`CheckNetIsolation`) for you, or you can apply it via an Administrator Command Prompt.

---

### 2. How does telemetry actually work? (No slow files!)
Telemetry doesn't go through disk files—writing and reading files on an SSD/HDD would indeed be way too slow. Racing games use one of two real-time mechanisms:

* **UDP Network Packets (what Forza Horizon 5 uses):** Roughly 60 times per second, FH5 packs a tiny, raw binary snapshot of your car's state (RPM, speed, gear, wheel slip, suspension travel, G-forces, etc.) into a **UDP datagram** and shoots it at the IP address and port you typed in. When set to `127.0.0.1`, that packet never even leaves your PC—Windows routes it through memory in sub-millisecond time. Because it's standard networking, it also lets an Xbox send telemetry over Wi-Fi/LAN to a PC running SimHub.
* **Shared Memory (what many other PC sims use):** Games like iRacing or Assetto Corsa use Windows *Memory-Mapped Files*. Despite the word "file" in the OS term, nothing is written to your drive; it is simply a shared block of **RAM** that the game writes to and SimHub reads from simultaneously at 60–360+ Hz.

*(Note: When SimHub asks to "configure" a game by editing a `.xml` or `.ini` file, that's just a one-time settings toggle to tell the game to turn its UDP or Shared Memory stream on.)*

---

### 3. How does the Next Level Racing HF8 work with SimHub vs. NLR's software?

#### How NLR's own software (HFS) works
Next Level Racing’s **HFS (Haptic Feedback Software)** is essentially a basic version of the same idea: it sits in the background, listens to telemetry from supported games (via UDP, Shared Memory, or game APIs), translates things like RPM or braking into vibration levels, and sends those commands to the pad over USB. However, HFS supports fewer games, offers fairly coarse presets/sliders, and historically felt clunky compared to third-party tools.

#### How SimHub works without NLR's software
You **do not** need NLR’s HFS software installed or running at all on PC. In fact, you *shouldn't* run both at once because they will fight over the USB device (and FH5 can only send UDP telemetry to one port/app at a time unless forwarded).

Instead, SimHub handles the whole pipeline itself:
1. **FH5** sends UDP telemetry -> **SimHub**.
2. **SimHub's "ShakeIt Motors"** module reads that telemetry and lets you map specific effects (ABS, wheel lock, gear shifts, RPM, road rumble, G-forces) to specific zones of the pad with custom response curves and intensities.
3. **SimHub** talks directly to the HF8 hardware over USB.

*(Side note: The HF8 also has a **3.5mm Audio Mode**—indicated by a flashing LED on the control dial, whereas USB Mode is a solid LED. Audio mode is meant for consoles or non-telemetry games and just rumbles based on bass frequencies in game audio, which is much vaguer than USB telemetry mode.)*

---

### 4. How does SimHub connect to the HF8, and is it "dashboard-based"?

#### SimHub isn't just for dashboards
SimHub originally became famous for putting custom digital dashboards on old phones, tablets, or spare screens (`Dash Studio`), so it's easy to assume it's a dashboard tool. In reality, it is a full **sim-racing middleware hub**. Dashboards are just one plugin/tab inside it; haptic motors (`ShakeIt Motors`), audio bass shakers (`ShakeIt Bass Shakers`), LED rev lights, Arduino wind simulators, and motion platforms are completely separate modules driven by the same central telemetry engine.

#### How SimHub talks to the HF8 hardware
There is no custom dashboard magic involved, and no proprietary NLR software layer required:
* Inside the HF8's control box is a microcontroller driving **8 independent vibration motors**.
* Next Level Racing actually built the HF8 on the same underlying USB electronics and communication protocol as an older haptic pad called the **Realteus ForceFeel**. (That's why, in SimHub under **ShakeIt Motors -> Motors Output**, you often activate **"ForceFeel Pad"** or **"Next Level Racing HF8"** depending on your SimHub version.)
* When plugged in via USB, Windows recognizes it using standard built-in USB device interfaces (no special NLR driver needed). SimHub simply knows the hardware's USB packet format: every update cycle, SimHub sends a tiny data packet straight down the USB cable containing 8 motor-speed values (0–100%) corresponding to the 8 pads in your seat.

___

now, for the pivot: is it possible to "hijack" the aforementioned device to
completely other purpose to achieve complete control of the input/output via
that udp port without building up a whole separate hardware/software setup? yes,
indeed this device just mentioned has audio input but it operates on some vague
principle that doesnt care that much of frequency and thus it may not be
suitable for the subtitute of woojer type thing, but neither would woojer be
(not sure, too expensive to find out) for this project? it now controls the
x-box controllers just adjusting timing and slighly intensity based on isolated
bass track; and as there is no freq cut-off in the hf8, then it would vibrate on
upper frequencies as well and not be synched to the software using it like the
xbox controller (or multiple) are in this neat software. attached are the main
code file and the research that one ai-system came up with when last the user
approached the subject matter.

___

**Yes—you can completely hijack the NLR HF8 over UDP for your `light_wave_tech` visualizer without building the custom PCB in `2026-10-19_notes.md`, and without installing NLR's software.**

In fact, the HF8 already *is* the hardware described in your `2026-10-19_notes.md` (an MCU + 8 PWM motor drivers + 8 ERM motors powered by an external power brick) packaged into a seat pad with a USB cable.

---

### 1. Why your instinct about the 3.5mm Audio Input (and Woojer) is spot-on
Even though your code already creates a clean `140 Hz` low-passed `lfe_filtered` channel inside `ROG_Theta_71_SUNO_load_and_EQ`—which *could* prevent upper-frequency bleed if routed to a spare soundcard jack—the HF8's **3.5mm Sound Capture Mode** has two fatal flaws for your project:
1. **No independent zones:** In 3.5mm audio mode, the HF8 fires **all 8 motors together** from the audio signal. You lose the ability to separate bass, snare, and hi-hat physically across your back and thighs.
2. **Audio buffer latency:** Your WASAPI stream is running at `sd.default.latency = 0.117` (117 ms), which is the whole reason you wrote `AV_SYNC_OFFSET = -0.117` and `Get_Rumble_Sync` to read pre-extracted stem keyframes (`_bass_keyframes.csv`, `_snare_keyframes.csv`, `_hihat_keyframes.csv`) ahead of the audio hardware.

By contrast, in **USB mode**, all 8 motors are individually addressable in real time.

---

### 2. How to "Hijack" the HF8 via UDP (Python $\rightarrow$ UDP $\rightarrow$ SimHub $\rightarrow$ HF8)
Instead of building an RP2040 + MOSFET board, you can let **SimHub run silently in the background purely as a free USB hardware driver**, while your Python script feeds it custom UDP packets on `127.0.0.1` instead of (or alongside) calling `XInputSetState`:

```text
[ *_keyframes.csv ]
        │
        ▼
[ Get_Rumble_Sync() in light_wave_tech ] ──► XboxControllerRumble (USB XInput)
        │
        └──► UDP packet (127.0.0.1) ──► SimHub (ShakeIt Motors) ──► HF8 (8 USB Zones)
```

You have **three ways** to send that UDP feed from Python into SimHub:

#### Option A: SimHub's Native "External Sim Integration" (`.simdef`) — *Cleanest*
Starting in SimHub 9.11.5, SimHub added an official **External Sim Integration** specifically for custom/non-public apps:
* You create a tiny `.simdef` contract (using SimHub's built-in definition editor) defining a UDP port and your own custom binary fields—for example, `bass`, `snare`, `hihat`, or even 8 raw floats (`motor_1` through `motor_8`).
* Your Python loop packs those floats with `struct.pack` and sends one tiny UDP packet per frame to `127.0.0.1:PORT`.
* In SimHub's **ShakeIt Motors**, you map each of your 8 HF8 zones (selected as `ForceFeel` / `Next Level Racing HF8`) directly to those custom fields using Custom Effects / JS / NCalc formulas.

#### Option B: `SimHubUDPConnector` Plugin — *Easiest Python Code (JSON)*
There is a popular open-source SimHub plugin (`SimHubUDPConnector`) that listens on any UDP port you configure for plain JSON key/value pairs. In Python, it's literally one line:
```python
sock.sendto(json.dumps({
    "bass": bass_force,
    "snare": snare_force,
    "hihat": hihat_force
}).encode(), ("127.0.0.1", UDP_PORT))
```
Those keys become immediately usable inside ShakeIt Motors.

#### Option C: Spoof Forza Horizon 5's UDP Packet — *Zero extra plugins*
If you want SimHub completely stock with zero `.simdef` or plugins, Python can impersonate FH5 by packing your values into FH5's little-endian `Data Out` UDP struct (`IsRaceOn = 1`) and firing it at SimHub's FH5 port (`5607`):
* Put `bass` into e.g. `CurrentEngineRpm` (or rear wheel slip/suspension travel), `snare` into `Brake` / `Accel`, `hihat` into `Throttle` / front wheel slip.
* *Downside:* SimHub's built-in racing effects expect car physics (RPM ratios, speed thresholds), so you'd still want to bypass presets with Custom ShakeIt Effects reading the raw telemetry properties directly. Options A and B are much cleaner because there's no fake car math in the middle.

---

### 3. Wait—what about talking directly to the HF8 over USB from Python (no SimHub)?
Just like your `2026-10-19_notes.md` notes for Choice A/B, you *might* wonder if you can skip SimHub completely and talk to the HF8 over USB straight from Python:
* **Why it's not plug-and-play:** Unlike Xbox controllers (where Windows includes `xinput1_4.dll`), Next Level Racing does not publish a public Python SDK or USB HID report spec for the HF8/ForceFeel.
* **How you *could* do it if you really wanted zero third-party apps:** Because the HF8 uses standard Windows USB HID (that's why SimHub doesn't need NLR's driver installed), you can plug it in, run **Wireshark + USBPcap** for 10 minutes while dragging each of the 8 motor test sliders in SimHub, record the HID Report ID and which 8 bytes control motors `0..7`, and then send that raw HID report straight from Python using `hidapi`.
* **Practical verdict:** Using SimHub via UDP as a silent hardware daemon takes 5 minutes to set up, avoids reverse-engineering USB HID descriptors, and gives you per-motor master gain sliders and quick testing tools—while Python still retains 100% control over the timing and isolation.

---

### 4. Specific Tweaks for `light_wave_tech_v1.1.10.py`
Looking at how your main loop is built, three things will make the HF8 feel razor-sharp instead of muddy:

1. **Keep your non-blocking hold/decay envelope in Python:**
   Your loop runs at `clock.tick(48)` (~20.8 ms per frame), and `Get_Rumble_Sync` outputs a `duration` of `0.05`–`0.08`s so short hits don't vanish in a single frame. Keep a similar non-blocking timer/decay envelope in Python before sending the float (`0.0`–`1.0`) over UDP, and **disable any smoothing/gamma filters inside SimHub's ShakeIt effect**, otherwise SimHub will smear your sharp `_bass_keyframes.csv` transients.
2. **Tune a dedicated sync offset:**
   Right now you use `audio_time_elapsed_rumble = int(((current_perf_time - start_time) + (AV_SYNC_OFFSET/2.0)) * 1000)` to account for the `117 ms` WASAPI latency minus Xbox motor spin-up. Because UDP $\rightarrow$ SimHub $\rightarrow$ HF8 USB adds a small hop (typically ~5–15 ms), make that offset an independent variable (e.g., `HF8_SYNC_OFFSET`) so you can dial the seat motors in to hit dead-on with the headphones.
3. **Exploit all 8 spatial zones:**
   With `XboxControllerRumble` you are stuck with 2 channels (`Left = Bass`, `Right = Snare/Hi-hat`). With the HF8's 8 zones, you can split your existing stem data spatially across your body:
   * **Thighs + Lower Seat (4 motors):** `current_amplitude_bass` (heavy low-end foundation)
   * **Mid/Lower Back (2 motors):** `current_amplitude_snare`
   * **Upper Back / Shoulders (2 motors):** `current_amplitude_hihat` (or your `sync_value_3` flash peaks)
