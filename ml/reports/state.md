# State in or out

Written by `uv run unstuk-state-check`; do not edit by hand. M5 spec section 4: `cosine-lr5e-05-typos-state` against its twin trained without state, `cosine-lr5e-05-typos`, on the 47 records of `data/state/test.jsonl` and on dev, each with its own dev-fitted temperatures. Intervals are paired 95% bootstrap intervals, with state minus without.

| Measure | With state | Without | Difference |
| --- | --- | --- | --- |
| State-test accuracy (clear lines) | 81.0% | 45.2% | +22.2% to +50.0% |
| Dev macro-F1 | 98.2% | 98.4% | -0.7% to +0.5% |

**State stays.** The rule: the state-test interval lies above 0, and the dev macro-F1 interval does not lie below 0.

## Each record

| Complaint | State | Label | With state | Without |
| --- | --- | --- | --- | --- |
| phone not making any noise at all | greyscale_on, ring_volume_zero | phone_not_ringing | phone_not_ringing | phone_not_ringing |
| phone not making any noise at all | data_saver_on | notifications_missing | notifications_missing | phone_not_ringing |
| phone not making any noise at all | brightness_low | phone_not_ringing, notifications_missing | phone_not_ringing | phone_not_ringing |
| everyone is angry because i never reply, the phone just sits there quiet | ring_volume_zero | phone_not_ringing | notifications_missing | notifications_missing |
| everyone is angry because i never reply, the phone just sits there quiet | data_saver_on, inversion_on | notifications_missing | notifications_missing | notifications_missing |
| phone stays quiet, nothing pops up, i miss everything | ringer_not_normal | phone_not_ringing | phone_not_ringing | notifications_missing |
| phone stays quiet, nothing pops up, i miss everything | data_saver_on | notifications_missing | notifications_missing | notifications_missing |
| ever since i updated the phone it doesnt alert me to anything | ring_volume_zero | phone_not_ringing | notifications_missing | notifications_missing |
| ever since i updated the phone it doesnt alert me to anything | data_saver_on | notifications_missing | notifications_missing | notifications_missing |
| The phone was in my bag all afternoon and I missed everything from my family | brightness_low, ringer_not_normal | phone_not_ringing | notifications_missing | notifications_missing |
| The phone was in my bag all afternoon and I missed everything from my family | data_saver_on | notifications_missing | notifications_missing | notifications_missing |
| My wife tried and tried to get me and my phone did nothing at all | ring_volume_zero | phone_not_ringing | phone_not_ringing | no_internet |
| My wife tried and tried to get me and my phone did nothing at all | data_saver_on, text_not_enlarged | notifications_missing | no_internet | no_internet |
| I think I pressed a button on the side and now the phone is totally quiet | offline_wifi_off, ring_volume_zero | phone_not_ringing | phone_not_ringing | phone_not_ringing |
| I think I pressed a button on the side and now the phone is totally quiet | data_saver_on | notifications_missing | notifications_missing | phone_not_ringing |
| My daughter says she sent me photos but I have not got them | inversion_on, offline_wifi_off | no_internet | notifications_missing | notifications_missing |
| My daughter says she sent me photos but I have not got them | bluetooth_off, dnd_on | notifications_missing | notifications_missing | notifications_missing |
| my screen looks weird and its hard to see anything | airplane_on, brightness_low | screen_too_dim | screen_too_dim | screen_too_dim |
| my screen looks weird and its hard to see anything | inversion_on | colours_wrong | colours_wrong | screen_too_dim |
| my photos look horrible all of a sudden | brightness_low | screen_too_dim | screen_too_dim | colours_wrong |
| my photos look horrible all of a sudden | greyscale_on | colours_wrong | colours_wrong | colours_wrong |
| It is very hard to read the words on my phone now | brightness_low | screen_too_dim | text_too_small | text_too_small |
| It is very hard to read the words on my phone now | greyscale_on | colours_wrong | text_too_small | text_too_small |
| something wrong with display, all looks faded | brightness_low | screen_too_dim | screen_too_dim | colours_wrong |
| something wrong with display, all looks faded | greyscale_on | colours_wrong | colours_wrong | colours_wrong |
| Screen not showing properly, like something is wrong with it | brightness_low, timeout_short | screen_too_dim | screen_too_dim | screen_too_dim |
| Screen not showing properly, like something is wrong with it | bluetooth_off, greyscale_on | colours_wrong | colours_wrong | screen_too_dim |
| Screen became unclear suddenly, what to do | brightness_low, ring_volume_zero | screen_too_dim | screen_too_dim | screen_too_dim |
| Screen became unclear suddenly, what to do | data_saver_on, inversion_on | colours_wrong | colours_wrong | screen_too_dim |
| Screen became unclear suddenly, what to do | ringer_not_normal | screen_too_dim, colours_wrong | colours_wrong | screen_too_dim |
| i pressed something and now my phone is acting strange | talkback_on | talkback_on | talkback_on | talkback_on |
| i pressed something and now my phone is acting strange | greyscale_on, ring_volume_zero | colours_wrong | colours_wrong | talkback_on |
| My phone has gone funny after I held the side buttons | ringer_not_normal, talkback_on | talkback_on | talkback_on | colours_wrong |
| My phone has gone funny after I held the side buttons | bluetooth_off, greyscale_on | colours_wrong | colours_wrong | colours_wrong |
| phone gone all strange suddenly, i didnt do anything | talkback_on | talkback_on | talkback_on | colours_wrong |
| phone gone all strange suddenly, i didnt do anything | greyscale_on | colours_wrong | colours_wrong | colours_wrong |
| phone not normal after my child played with it | brightness_low, talkback_on | talkback_on | screen_too_dim | colours_wrong |
| phone not normal after my child played with it | greyscale_on | colours_wrong | colours_wrong | colours_wrong |
| phone not normal after my child played with it |  | talkback_on, colours_wrong | colours_wrong | colours_wrong |
| Kindly help, phone become strange after I pressed volume buttons | talkback_on | talkback_on | talkback_on | talkback_on |
| Kindly help, phone become strange after I pressed volume buttons | inversion_on | colours_wrong | colours_wrong | talkback_on |
| Kindly help, phone become strange after I pressed volume buttons |  | talkback_on, colours_wrong | talkback_on | talkback_on |
| some little man icon popped up and i tapped it and now phone is strange | talkback_on | talkback_on | talkback_on | talkback_on |
| some little man icon popped up and i tapped it and now phone is strange | greyscale_on, offline_wifi_off | colours_wrong | colours_wrong | talkback_on |
| the phone went odd after my cat walked on it | talkback_on | talkback_on | talkback_on | colours_wrong |
| the phone went odd after my cat walked on it | greyscale_on | colours_wrong | colours_wrong | colours_wrong |
| the phone went odd after my cat walked on it |  | talkback_on, colours_wrong | talkback_on | colours_wrong |
