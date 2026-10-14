# v2_32-bit_pygame_mini_audio_player.py

# XboxControllerRumble opens up vibrotactile music perception
# see Haptics_in_Multisensory_Music_Experience_(vibrotactile).md

# 2.0 Stereo        >> SUNO_load_and_EQ()
# 7.1 Multi-Channel >> ROG_Theta_71_SUNO_load_and_EQ 
# data passed onward like so: sd.play(my_song_array, samplerate=sample_rate, mapping=[1, 2, 3, 4, 5, 6, 7, 8])


import keyboard
import random
import time

from scipy.signal import butter, lfilter, sosfiltfilt
import pyloudnorm as pyln
import sounddevice as sd
import soundfile as sf
import numpy as np

import ctypes

#______________________________________________________________________________________________________
#___CONTROLLER_________________________

# --- WINDOWS API C-STRUCTS FOR XBOX RUMBLE ---
class XINPUT_VIBRATION(ctypes.Structure):
    _fields_ = [("wLeftMotorSpeed", ctypes.c_ushort),
                ("wRightMotorSpeed", ctypes.c_ushort)]

# Load the Windows XInput DLL
try:
    xinput = ctypes.windll.xinput1_4  # Windows 8, 10, 11
except OSError:
    xinput = ctypes.windll.xinput1_3  # Windows 7

class XboxControllerRumble:
    def __init__(self, controller_id=0):
        self.controller_id = controller_id
        
        # Track timers and current forces independently!
        self.left_end_time = 0.0
        self.right_end_time = 0.0
        self.current_left = 0.0
        self.current_right = 0.0

        self.is_connected = self.check_connection()

    def check_connection(self):
        """Tests if the controller is plugged in by sending a dummy command."""
        vibration = XINPUT_VIBRATION(0, 0)
        result = xinput.XInputSetState(self.controller_id, ctypes.byref(vibration))
        
        # 0 means ERROR_SUCCESS. Anything else means disconnected.
        return result == 0

    def _apply_hardware(self):
        """Internal function that sends both current states to the controller."""

        if not self.is_connected:
            return

        vibration = XINPUT_VIBRATION()
        vibration.wLeftMotorSpeed = int(self.current_left * 65535)
        vibration.wRightMotorSpeed = int(self.current_right * 65535)

        result = xinput.XInputSetState(self.controller_id, ctypes.byref(vibration))
        
        # If the controller gets unplugged mid-game, update our tracker
        if result != 0 and self.is_connected:
            print("Controller disconnected!")
            self.is_connected = False
            
        # If the controller gets plugged back in mid-game, update our tracker
        elif result == 0 and not self.is_connected:
            print("Controller connected!")
            self.is_connected = True

    def rumble_left(self, force, duration):
        """Turns on the Left motor WITHOUT affecting the Right motor."""
        self.current_left = max(0.0, min(1.0, force))
        self.left_end_time = time.time() + duration
        self._apply_hardware()

    def rumble_right(self, force, duration):
        """Turns on the Right motor WITHOUT affecting the Left motor."""
        self.current_right = max(0.0, min(1.0, force))
        self.right_end_time = time.time() + duration
        self._apply_hardware()

    def update(self):
        """Checks timers independently and turns off motors only if their specific time is up."""
        now = time.time()
        changed = False
        
        # Check left motor
        if self.current_left > 0.0 and now >= self.left_end_time:
            self.current_left = 0.0
            changed = True
            
        # Check right motor
        if self.current_right > 0.0 and now >= self.right_end_time:
            self.current_right = 0.0
            changed = True
            
        # Only talk to the controller hardware if something actually finished
        if changed:
            self._apply_hardware()
            
    def stop(self):
        self.current_left = 0.0
        self.current_right = 0.0
        self._apply_hardware()

#______________________________________________________________________________________________________
#___AUDIO_DSP__________________________

def get_audio_len(audio_path):
    # This reads the metadata without loading the whole heavy file into memory
    info = sf.info(audio_path)
    return info.duration  # Returns length in seconds

# --- DSP Crossover Function ---
def create_lowpass_filter(cutoff, fs, order=4):
    """
    Creates a Butterworth Low-Pass Filter.
    Standard THX crossover is 80Hz, standard Dolby LFE limit is 120Hz.
    Order=4 creates a steep 24dB/octave slope.
    """
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

#__FOR_STEREO_WIDEN_PURPOSES::SUNO_load_and_EQ__
from stereo_widener.velvet import *
from stereo_widener.allpass import *
from stereo_widener.widener import *

def SUNO_load_and_EQ(playlist_type, audio_path, target_lufs=-13.0, bass_db=0.0, mid_db=0.0, treble_db=0.0):
    # 1. Read the 32-bit WAV as a 32-bit float array
    # float32 gives 144+ dB of dynamic range, perfect for DSP and WASAPI
    data, fs = sf.read(audio_path, dtype='float32')

    # 2. Measure the current LUFS
    meter = pyln.Meter(fs)
    current_loudness = meter.integrated_loudness(data)

    # This finds the volume variance and normalizes it.
    delta_db = target_lufs - current_loudness

    # Adjust your predefined EQ values with the delta
    adjusted_bass_db = bass_db + delta_db
    adjusted_mid_db = mid_db + delta_db
    adjusted_treble_db = treble_db + delta_db

    print(f"Original LUFS: {current_loudness:.2f} | Delta applied: {delta_db:+.2f} dB")
    print(f"New EQ -> Bass: {adjusted_bass_db:.2f}, Mid: {adjusted_mid_db:.2f}, Treble: {adjusted_treble_db:.2f}")

    log_file = "LOG_LUFs.txt"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"Original: {current_loudness:.2f} LUFS | Delta: {delta_db:+.2f} dB | {audio_path}\n")
    
    # 2. Design crossover filters (2nd order Butterworth)
    bass_freq = 170 #250.0    # Adjust to target your specific bass threshold
    treble_freq = 4000.0 # Adjust for high-end sparkle
    
    sos_bass = butter(2, bass_freq, btype='low', fs=fs, output='sos')
    sos_mid = butter(2, [bass_freq, treble_freq], btype='bandpass', fs=fs, output='sos')
    sos_treble = butter(2, treble_freq, btype='high', fs=fs, output='sos')
    
    # 3. Apply zero-phase filtering (axis=0 keeps stereo channels intact)
    print("Applying EQ filtering...")

    # sosfiltfilt applies the filter forward and backward, creating a 4th-order Linkwitz-Riley response
    bass_sig = sosfiltfilt(sos_bass, data, axis=0)
    mid_sig = sosfiltfilt(sos_mid, data, axis=0)
    treble_sig = sosfiltfilt(sos_treble, data, axis=0)

    if playlist_type == "CORE" or playlist_type == "SUMMER":
        decorr_type = DecorrelationType.ALLPASS
        beta_init = 0.40 # >> V5 | V6: 0.07-0.10 IF NEED BE
        stereo_widener = StereoWidenerBroadband(treble_sig, fs, decorr_type, beta_init)
        treble_sig = stereo_widener.process()
 
        # NOT_SURE_IF_THIS_BRINGS_ANYTHING_EXTRA_SINCE_EQ_ALREADY
        beta_init = 0.20 # >> V5 | V6: 0.07-0.10 IF NEED BE
        stereo_widener = StereoWidenerBroadband(mid_sig, fs, decorr_type, beta_init)
        mid_sig = stereo_widener.process()
    
    # 4. Convert dB adjustments to linear gain multipliers
    gain_bass = 10 ** (bass_db / 20)
    gain_mid = 10 ** (mid_db / 20)
    gain_treble = 10 ** (treble_db / 20)
    
    # 5. Mix the adjusted bands back together
    eq_data = (bass_sig * gain_bass) + (mid_sig * gain_mid) + (treble_sig * gain_treble)

    # 6. Prevent clipping
    # We target 0.99 (-0.1 dBFS) to safely prevent intersample peaking
    target_max = 0.99
    max_val = np.max(np.abs(eq_data))

    if max_val > target_max:
        scale_factor = target_max / max_val
        eq_data = eq_data * scale_factor

        reduction_db = 20 * np.log10(scale_factor)
        print(f"Auto-normalized to prevent clipping (reduced by {abs(reduction_db):.2f} dB)")
        with open("LOG_AUTO_NORMALs.txt", "a", encoding="utf-8") as f:
            f.write(f"Reduced by {abs(reduction_db):.2f} dB (Peak was {max_val:.2f}): {audio_path}\n")

    # 2. Measure the current LUFS
    meter = pyln.Meter(fs)
    current_loudness = meter.integrated_loudness(eq_data)
    normalized_eq_data = pyln.normalize.loudness(eq_data, current_loudness, target_lufs)
    delta_db = target_lufs - current_loudness
    print(f"delta_db: {abs(delta_db):.2f} dB)")
    
    audio_length_seconds = len(data) / fs
    return normalized_eq_data, fs, audio_length_seconds
#    return eq_data, fs, audio_length_seconds

# >>> SAVE OUTPUT TO FILE infinite.quantum: https://aistudio.google.com/prompts/1ecQwH8X1aWJp8nBW1EQUZYtaKcJRC_AZ

def ROG_Theta_71_SUNO_load_and_EQ(playlist_type, audio_path, target_lufs=-13.0, bass_db=0.0, mid_db=0.0, treble_db=0.0):
    # 1. Read the audio
    data, fs = sf.read(audio_path)
    if data.ndim == 1:
        data = np.expand_dims(data, axis=1)
        
    # 2. Measure the current LUFS
    meter = pyln.Meter(fs)
    current_loudness = meter.integrated_loudness(data)

    # This finds the volume variance and normalizes it.
    delta_db = target_lufs - current_loudness

    # Adjust your predefined EQ values with the delta
    adjusted_bass_db = bass_db + delta_db
    adjusted_mid_db = mid_db + delta_db
    adjusted_treble_db = treble_db + delta_db

    print(f"Original LUFS: {current_loudness:.2f} | Delta applied: {delta_db:+.2f} dB")
    print(f"New EQ -> Bass: {adjusted_bass_db:.2f}, Mid: {adjusted_mid_db:.2f}, Treble: {adjusted_treble_db:.2f}")

    log_file = "LOG_LUFs.txt"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"Original: {current_loudness:.2f} LUFS | Delta: {delta_db:+.2f} dB | {audio_path}\n")

    # 2. Design crossover filters (2nd order Butterworth)
    bass_freq = 170 #250.0    # Adjust to target your specific bass threshold
    treble_freq = 4000.0 # Adjust for high-end sparkle
    
    sos_bass = butter(2, bass_freq, btype='low', fs=fs, output='sos')
    sos_mid = butter(2, [bass_freq, treble_freq], btype='bandpass', fs=fs, output='sos')
    sos_treble = butter(2, treble_freq, btype='high', fs=fs, output='sos')
    
    print("Applying EQ filtering...")
    # 3. Apply zero-phase filtering (axis=0 keeps stereo channels intact)
    # sosfiltfilt applies the filter forward and backward, creating a 4th-order Linkwitz-Riley response
    bass_sig = sosfiltfilt(sos_bass, data, axis=0)
    mid_sig = sosfiltfilt(sos_mid, data, axis=0)
    treble_sig = sosfiltfilt(sos_treble, data, axis=0)

    # 4. Convert dB adjustments to linear gain multipliers
    gain_bass   = 10 ** (bass_db / 20)
    gain_mid    = 10 ** (mid_db / 20)
    gain_treble = 10 ** (treble_db / 20)

    eq_data = (bass_sig * gain_bass) + (mid_sig * gain_mid) + (treble_sig * gain_treble)

    if 1: #playlist_type == "CORE" or playlist_type == "SUMMER":
        decorr_type = DecorrelationType.ALLPASS
        #beta_init = 0.50 # >> V5 | V6: 0.07-0.10 IF NEED BE
        beta_init = 0.15
        stereo_widener = StereoWidenerBroadband(treble_sig, fs, decorr_type, beta_init)
        treble_sig = stereo_widener.process()
 
        # NOT_SURE_IF_THIS_BRINGS_ANYTHING_EXTRA_SINCE_EQ_ALREADY
        stereo_widener = StereoWidenerBroadband(mid_sig, fs, decorr_type, beta_init)
        mid_sig = stereo_widener.process()
    
    # 5. Mix the adjusted bands back together
    eq_data_stereo_widener = (bass_sig * gain_bass) + (mid_sig * gain_mid) + (treble_sig * gain_treble)
    
    # 6. Prevent clipping (BUG FIX: Check and scale BOTH arrays)
    # We target 0.99 (-0.1 dBFS) to safely prevent intersample peaking
    target_max = 0.99 
    
    max_val_standard = np.max(np.abs(eq_data))
    max_val_widened = np.max(np.abs(eq_data_stereo_widener))
    global_max = max(max_val_standard, max_val_widened) # Find highest peak across everything

    if global_max > target_max:
        scale_factor = target_max / global_max
        # Apply the reduction to both sets of audio!
        eq_data = eq_data * scale_factor
        eq_data_stereo_widener = eq_data_stereo_widener * scale_factor
        
        reduction_db = 20 * np.log10(scale_factor)
        print(f"Auto-normalized to prevent clipping (reduced by {abs(reduction_db):.2f} dB)")
        with open("LOG_AUTO_NORMALs.txt", "a", encoding="utf-8") as f:
            f.write(f"Reduced by {abs(reduction_db):.2f} dB (Peak was {global_max:.2f}): {audio_path}\n")

    # 3. Build the 8-channel array
    # sounddevice expects float32 arrays natively, which is great!
    padded_audio = np.zeros((eq_data.shape[0], 8), dtype=np.float32)
  
    left  = eq_data[:, 0]
    right = eq_data[:, 1]
    mono = (left + right) * 0.5

    left_surround  = eq_data_stereo_widener[:, 0]
    right_surround = eq_data_stereo_widener[:, 1]

    # Generate the filter coefficients for 120Hz at whatever the sample rate is (e.g., 48000)
    mono_for_sub = (left + right) * 0.8
    b, a = create_lowpass_filter(cutoff=140.0, fs=fs, order=4)

    # Apply the filter mathematically to the mono signal
    lfe_filtered = lfilter(b, a, mono_for_sub)
    
    # Map to 7.1 Standard Windows Layout
    padded_audio[:, 0] = left   	# Front Left
    padded_audio[:, 1] = right  	# Front Right

    padded_audio[:, 2] = mono   	# Center
    padded_audio[:, 3] = lfe_filtered   # Subwoofer (LFE)

    padded_audio[:, 4] = left_surround 	# Rear Left
    padded_audio[:, 5] = right_surround	# Rear Right

    padded_audio[:, 6] = left   	# Side Left
    padded_audio[:, 7] = right  	# Side Right
    
    # Return the array, the sample rate, and the length of the audio in seconds
    audio_length_seconds = len(padded_audio) / fs
    return padded_audio, fs, audio_length_seconds


exit_signal = False
PLAYLIST = True

EVERYTHING         = False
CORE_EDITION       = True
SUMMER_EDITION     = False
PSY_TRANCE_EDITION = False
HARDWAVE_EDITION   = False
CUSTOM_EDITION     = False

# DUE TO THE LACK OF STORAGE 3 PLACES
audio_base_folder_1 = "H:/SUNO_32-BIT_AUDIO" # CORE + CUSTOM
audio_base_folder_2 = "C:/SUNO_32-BIT_AUDIO" # SUMMER
audio_base_folder_3 = "F:/SUNO_32-BIT_AUDIO" # HARDWAVE + PSY_TRANCE

from audio_vars_playlist import *

# 1. Map editions to their corresponding lists, types, and base folders.
playlist_configs = [
    (CORE_EDITION,       SUNO_AUDIO_CORE,       "CORE",       audio_base_folder_1),
    (SUMMER_EDITION,     SUNO_AUDIO_SUMMER,     "SUMMER",     audio_base_folder_2),
    (PSY_TRANCE_EDITION, SUNO_AUDIO_PSY_TRANCE, "PSY_TRANCE", audio_base_folder_3),
    (HARDWAVE_EDITION,   SUNO_AUDIO_HARDWAVE,   "HARDWAVE",   audio_base_folder_3),
    (CUSTOM_EDITION,     SUNO_AUDIO_CUSTOM,     "CUSTOM",     audio_base_folder_1),
]

songs_all_random = []

# 2. Dynamically build the list
for is_active, song_list, p_type, base_folder in playlist_configs:
    # If this specific edition is active, OR we want everything:
    if is_active or EVERYTHING:
        
        # Attach the metadata to every filename on the fly
        songs_all_random.extend([
            {"filename": f, "type": p_type, "base_folder": base_folder} 
            for f in song_list
        ])
        
        # If we are NOT in EVERYTHING mode, stop checking after the first match.
        # This perfectly mimics your original 'if/elif' chain logic.
        if not EVERYTHING:
            break

# Shuffle the dictionaries
random.shuffle(songs_all_random)
print(f"{len(songs_all_random)} items in playlist")


if PLAYLIST:
    for i, song_data in enumerate(songs_all_random):
        # Extract the values from our dictionary
        audio_file = song_data["filename"]
        playlist_type = song_data["type"]
        base = song_data["base_folder"]
    
        # Construct the path dynamically! 
        # Because the metadata travels with the file, no if/elif statements are needed.
        audio_path = f"{base}/{playlist_type}/{audio_file}"
        print(f"{i+1}/{len(songs_all_random)} >> audio_path: {audio_path}")

        audio_len = get_audio_len(audio_path)
        print(f"audio_len: {audio_len}")
        audio_time_elapsed = 0

        # JBL
        my_song_array, sample_rate, audio_len_seconds = SUNO_load_and_EQ(playlist_type, audio_path, bass_db=9.5, mid_db=0.5, treble_db=2.7)

        # AKG
#        my_song_array, sample_rate, audio_len_seconds = SUNO_load_and_EQ(playlist_type, audio_path, bass_db=7.8, mid_db=1.8, treble_db=3.5)

        inferred_channels = my_song_array.shape[1] if my_song_array.ndim > 1 else 1
        inferred_dtype = my_song_array.dtype.name

        # Query the WASAPI host API directly for the default output device
        try:
            # Retrieve a tuple of all available host APIs
            all_hostapis = sd.query_hostapis()

            # Find the dictionary where 'WASAPI' is in the name
            wasapi_info = next((api for api in all_hostapis if 'WASAPI' in api['name']), None)

            # If we didn't find it, trigger the except block below
            if wasapi_info is None:
                raise ValueError("WASAPI is not available on this system.")

            wasapi_out_index = wasapi_info['default_output_device']
    
            # Get info on that specific device for your print statements
            device_info = sd.query_devices(wasapi_out_index)
    
            print(f"--- CURRENT PLAYBACK SETTINGS ---")
            print(f"Device Name : {device_info['name']}")
            print(f"Host API    : {wasapi_info['name']} ({wasapi_out_index})")
            print(f"Sample Rate : {sample_rate} Hz (Requested)")
            print(f"Channels    : {inferred_channels}")
            print(f"Format      : {inferred_dtype}")
            print(f"Latency     : {device_info['default_low_output_latency']*1000:.1f} ms - {device_info['default_high_output_latency']*1000:.1f} ms")
            print(f"---------------------------------")

            # You can either set it as the global default:
            sd.default.device = wasapi_out_index
    
        except ValueError:
            print("WASAPI is not available on this system.")


        # Initialize our non-blocking rumble manager
        rumble = XboxControllerRumble(controller_id=0)
    
        # Play the audio; this directly interfaces with WASAPI/DirectSound
        if inferred_channels > 2:
            sd.play(my_song_array, samplerate=sample_rate, mapping=[1, 2, 3, 4, 5, 6, 7, 8])
        else:
            sd.play(my_song_array, samplerate=sample_rate)

        start_time = time.perf_counter()
        running = True

        while running:

            current_perf_time = time.perf_counter()
            audio_time_elapsed = int((current_perf_time - start_time) * 1000)

            if audio_time_elapsed >= (audio_len*1000):
                running = False

            # Check if ESC is pressed (works even if terminal is minimized!)
            if keyboard.is_pressed('esc'):
                print("Skipping track...")
                running = False
                time.sleep(0.3)  # Tiny delay so you don't accidentally skip 5 songs in a row

            # Exit the entire player completely
            if keyboard.is_pressed('x'):
                print("Exiting player...")
                exit_signal = True
                running = False
                time.sleep(0.3)

            # 3. CRITICAL: Prevent the while-loop from maxing out your CPU!
            time.sleep(0.05)


            """ CONTINUE WORKING ON PORTING THIS FUNCTIONALITY HERE
                #______________________________________________________________________________________________________
                #___APPLY_CONTROLLER_RUMBLE___(vibrotactile)

                # 1. Initialize variables for this specific frame
                target_left_force = 0.0
                target_left_duration = 0.0
                target_right_force = 0.0
                target_right_duration = 0.0

                # --- BASS (Left Motor) ---
                if apply_glitch_1 > 0.0:
                    if current_amplitude_bass > 0.5:
                        target_left_duration = 0.08
                        target_left_force = 1.0
                    elif current_amplitude_bass > 0.1:
                        target_left_duration = 0.05
                        target_left_force = 0.2 + current_amplitude_bass

                # --- SNARE (Right Motor) ---
                if apply_glitch_2 > 0.0:
                    if current_amplitude_snare > 0.6:
                        target_right_duration = 0.08
                        target_right_force = 1.0
                    elif current_amplitude_snare > 0.1:
                        target_right_duration = 0.05
                        target_right_force = 0.2 + current_amplitude_snare

                # --- HI-HAT (Right Motor) ---
                if apply_glitch_3 > 0.0:
                    temp_force = 0.0
                    temp_duration = 0.0
    
                    if current_amplitude_hihat > 0.6:
                        temp_duration = 0.08
                        temp_force = 1.0
                    elif current_amplitude_hihat > 0.1:
                        temp_duration = 0.05
                        temp_force = 0.2 + current_amplitude_hihat
        
                    # We use the higher value to ensure a weak hi-hat doesn't overwrite a heavy snare!
                    if temp_force > target_right_force:
                        target_right_force = temp_force
                        target_right_duration = temp_duration

                # 2. Finally, apply the requested rumbles!

                if target_left_force > 0.7 and target_right_force > 0.7:
                    rumble.rumble_left(force=1.0, duration=0.08)
                    rumble.rumble_right(force=1.0, duration=0.08)
                else:
                    if target_left_force > 0.0:
                        rumble.rumble_left(force=target_left_force, duration=target_left_duration)

                    if target_right_force > 0.0:
                        rumble.rumble_right(force=target_right_force, duration=target_right_duration)

                # 3. Always run update to handle shutting them down when timers expire
                rumble.update()"""

        if exit_signal:
            break

        # 5. Cleanly shut down the mixer when done
        sd.stop()               # Instantly stops hardware playback
        del my_song_array       # Free up RAM


