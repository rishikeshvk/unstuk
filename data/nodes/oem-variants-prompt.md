# OEM label variants prompt, v1

Written by a fresh agent that reads only this prompt and writes only its sheet, so it never sees our selector files
(the Moto file is the test).

```text
Do not read any files other than this one and do not run any commands. Use exactly one tool after reading: the
Write tool, once, to save the result to /home/user/unstuk/data/nodes/sheets/oem-variants.txt. Then reply only "done".

I need the English labels that Android phone makers show for some Quick Settings tiles and Settings rows, from your
own knowledge. Phone makers: samsung (One UI), xiaomi (HyperOS / MIUI), oppo (ColorOS), vivo (OriginOS / Funtouch
OS), oneplus (OxygenOS). Include British or Indian English spellings where the phone shows them (for example
"Aeroplane mode", "Colour inversion"). Only give labels you are fairly confident a real phone shows; skip a maker if
you are unsure. Several labels per maker are fine when versions differ.

Items (id: what it is):
- airplane_mode: the switch that turns airplane mode on and off
- dnd: the switch for Do Not Disturb
- mobile_data: the switch for mobile data
- wifi: the switch for Wi-Fi
- data_saver: the switch for the data-saving mode
- inversion: the switch that inverts the screen colours
- auto_rotate: the switch that lets the screen rotate
- bluetooth: the switch for Bluetooth
- talkback: the screen reader setting that reads the screen aloud
- hotspot: the switch for the mobile hotspot
- flashlight: the switch for the torch
- location: the switch for location
- battery_saver: the switch for the battery-saving mode
- nfc: the switch for NFC
- screen_record: the screen recorder tile
- dark_mode: the switch for the dark theme
- eye_comfort: the warm night-time screen tint
- cast: the switch for casting or screen mirroring
- sound_mode: the tile that switches sound, vibrate and mute
- qr_scanner: the QR code scanner tile

Write the file in only this plain-text format, with nothing before or after it and no code fences, one header per
item and one line per label:

## airplane_mode
samsung | Airplane mode
samsung | Flight mode
...
```
