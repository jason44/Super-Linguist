import pyaudio

pa = pyaudio.PyAudio()

def get_loopback_info():
    print("\n=== Audio Input Devices ===\n")

    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        
        # Only display input-capable devices
        if info.get('maxInputChannels', 0) > 0:
            print(f"Index: {i}")
            print(f" Name: {info['name']}")
            print(f" Channels: {info['maxInputChannels']}")
            print(f" Host API: {pa.get_host_api_info_by_index(info['hostApi'])['name']}")
            print("-" * 40)

TARGET_NAME = "Monitor of Starship/Matisse HD Audio Controller Analog Stereo"
device_index = None
def get_loopback_id_by_name():
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        name = info.get("name", "")
        
        if info.get("maxInputChannels", 0) > 0 and TARGET_NAME.lower() in name.lower():
            print(f"Matched loopback device: {name} (index {i})")
            device_index = i
            break



get_loopback_id_by_name()