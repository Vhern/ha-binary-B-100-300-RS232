# Binary B-100/300 RS232 Integration for Home Assistant

Custom Home Assistant integration for controlling and monitoring **Binary B-100 / B-300 Series HDMI Matrix Switchers** via RS232.

✨ Features:
- Choose between 4x4 or 8x8 model during setup
- Select entities for each output
- Power switch entities for each output
- Real-time status updates using STMAP polling
- Full RS232 command support
- Reliable queued serial communication

---

## Installation

### 1. Prerequisites
- [HACS](https://hacs.xyz/) installed in Home Assistant
- Your Binary Matrix connected through a USB-RS232 adapter or serial-over-IP bridge

### 2. Add this repository to HACS
1. In Home Assistant go to **HACS → Integrations**  
2. Click the 3-dot menu (top right) → **Custom repositories**  
3. Paste this URL: https://github.com/Vhern/ha-binary-B-100-300-RS232  
4. Select **Integration** as the category  
5. Click **Add**

### 3. Install the integration
1. After adding the repo, search for **Binary B-100/300 RS232** in HACS  
2. Install the latest release (e.g. `0.1.0`)  
3. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**  
2. Search for **Binary B-100/300 RS232**  
3. Enter:
- **Matrix Size** (4x4 or 8x8)  
- **Serial Port** (e.g. `/dev/ttyUSB0`)  
- **Baud Rate** (default `9600`)  
- **Poll Interval** (seconds between polls, default 5s)

Entities will be created for:
- Each output as a select entity (`select.binary_matrix_output_X_source`)  
- Each output power switch (`switch.binary_matrix_output_X_power`)  

---

## Example Use

- **Route inputs to outputs** directly from Home Assistant UI or automations  
- **Turn outputs on/off** or **cycle through inputs**  
- **Control matrix power** or **restore factory defaults**  
- **Use automations** to sync matrix routing with other AV devices

---

## Known Limitations
- RS232 only (no Telnet support)  
- Tested on Binary B-100-4x4 and B-300-8x8 models

---

## Issues / Feedback
Open an [issue](https://github.com/Vhern/ha-binary-B-100-300-RS232/issues) on GitHub with details. PRs are welcome!

---

## Credits
- Developed by [@Vhern](https://github.com/Vhern)  
- Based on Binary B-100 / B-300 RS232 protocol documentation
