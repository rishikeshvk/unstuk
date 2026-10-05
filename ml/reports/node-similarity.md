# Node-label similarity

Written by `uv run unstuk-node-similarity`; do not edit by hand. Frozen bge-small picks the option whose vector is closest to the question's; M3's string baseline matches labels known from AOSP and the Pixel. Dev is Xiaomi wording, the test is the Moto's screens. Dev intervals are 95% bootstrap intervals.

| Method | Options | Dev (132) | 95% interval | Test (10) |
| --- | --- | --- | --- | --- |
| String baseline | as shown | 90.9% | 85.6% to 95.5% | 8/10 |
| Similarity | as shown | 82.6% | 76.5% to 88.6% | 8/10 |
| String baseline | cut at ',' or '.' | 90.9% | 85.6% to 95.5% | 9/10 |
| Similarity | cut at ',' or '.' | 82.6% | 76.5% to 88.6% | 8/10 |

## Each test question

| Question | Answer | String baseline, as shown | Similarity, as shown | String baseline, cut at ',' or '.' | Similarity, cut at ',' or '.' |
| --- | --- | --- | --- | --- | --- |
| airplane_mode | `Aeroplane mode, Off` | ✓ `Aeroplane mode, Off` | ✓ `Aeroplane mode, Off` | ✓ `Aeroplane mode` | ✓ `Aeroplane mode` |
| auto_rotate | `Auto-rotate, Off` | ✓ `Auto-rotate, Off` | ✓ `Auto-rotate, Off` | ✓ `Auto-rotate` | ✓ `Auto-rotate` |
| bluetooth | `Bluetooth, Off` | ✓ `Bluetooth, Off` | ✓ `Bluetooth, Off` | ✓ `Bluetooth` | ✓ `Bluetooth` |
| data_saver | `Data Saver, Off` | ✓ `Data Saver, Off` | ✓ `Data Saver, Off` | ✓ `Data Saver` | ✓ `Data Saver` |
| dnd | `Turn off now` | ✗ `Do Not Disturb` | ✗ `What can interrupt Do Not Disturb` | ✗ `Do Not Disturb` | ✗ `What can interrupt Do Not Disturb` |
| dnd | `Do Not Disturb, Off` | ✓ `Do Not Disturb, Off` | ✓ `Do Not Disturb, Off` | ✓ `Do Not Disturb` | ✓ `Do Not Disturb` |
| inversion | `Colour inversion, Off` | ✓ `Colour inversion, Off` | ✓ `Colour inversion, Off` | ✓ `Colour inversion` | ✓ `Colour inversion` |
| mobile_data | `Mobile data, 5G+` | ✓ `Mobile data, 5G+` | ✓ `Mobile data, 5G+` | ✓ `Mobile data` | ✓ `Mobile data` |
| talkback | `TalkBack` | ✓ `TalkBack` | ✗ `Screen reader` | ✓ `TalkBack` | ✗ `Screen reader` |
| wifi | `Wi-Fi, Off` | none | ✓ `Wi-Fi, Off` | ✓ `Wi-Fi` | ✓ `Wi-Fi` |
