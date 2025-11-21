import soundcard as sc
import numpy as np

# 1. List all microphones, including monitor/loopback sources
mics = sc.all_microphones(include_loopback=True)

# 2. Identify the correct monitor source
# You will likely need to check the names (mics[i].name) to find the correct one
# For example, let's assume the correct monitor is at index 1 in the list:
# You should replace 'Monitor of Built-in Audio Analog Stereo' with your actual monitor source name
monitor_name = 'Monitor of Starship/Matisse HD Audio Controller Analog Stereo'
speaker_monitor = sc.get_microphone(monitor_name, include_loopback=True)

if speaker_monitor:
    print(f"Recording from: {speaker_monitor.name}")
    samplerate = 44100
    duration_seconds = 5
    numframes = samplerate * duration_seconds
    
    # 3. Record the audio
    with speaker_monitor.recorder(samplerate=samplerate) as mic:
        data = mic.record(numframes=numframes)
        
    # 'data' now contains the recorded speaker output as a NumPy array (frames x channels)
    print(f"Recorded data shape: {data.shape}")
    
    # Optional: Save the data to a WAV file using another library like 'scipy.io.wavfile'
    import scipy.io.wavfile as wavfile
    wavfile.write('speaker_output.wav', samplerate, data)
else:
    print("Could not find the specified monitor source.")