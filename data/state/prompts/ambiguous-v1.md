# State-slice prompt, v1

Complaints that the words alone can't settle between two problems (M3 spec section 8). A fresh agent writes them,
reading only this prompt and writing only its sheet; a second blind agent then drops any text the words settle.

```text
Do not read any files other than this one and do not run any commands. Use exactly one tool after reading:
the Write tool, once, to save your messages to /home/user/unstuk/data/state/sheets/ambiguous.txt. Then reply only
"done".

Context: a phone help app for people who are not comfortable with technology. They type their phone trouble into a
box in their own words. I need realistic messages that are genuinely unclear: a careful reader could not tell which
of two problems the person has, because the person describes the effect and not the cause. The app will look at
the phone's settings to decide. The messages are invented, not from real people.

For each of the five pairs below, write exactly 25 messages that fit BOTH problems of the pair equally well. Avoid
any word that would settle it (listed under "Avoid"). Vary the writer: teenagers, adults, people over seventy,
people whose English is a second language, people writing Indian English; short and long; some with typos; some
mentioning an app or what happened just before.

Never write about the screen turning sideways, the clock, time or date, or hearing or being heard during a call.

Pairs:
1. no_internet, wifi_no_load: nothing online works (could be mobile data or airplane mode off, or Wi-Fi that
   shows connected but loads nothing). Avoid: saying Wi-Fi is connected or off, airplane, mobile data, bars.
2. phone_not_ringing, notifications_missing: the phone stays silent and things are missed (could be calls or
   messages). Avoid: naming calls, ringing, messages, notifications or a specific app.
3. no_internet, notifications_missing: things from people or apps are not coming through (could be no internet
   at all, or alerts held back). Avoid: saying whether websites load, naming sound or alerts.
4. screen_too_dim, colours_wrong: the screen looks wrong and hard to look at (could be too dark, or grey or
   inverted). Avoid: naming colours, grey, black and white, brightness, dark or dim.
5. talkback_on, colours_wrong: the phone suddenly behaves or looks strange after something was pressed (could be
   the phone talking and needing double taps, or the colours changing). Avoid: talking, voice, double tap,
   colours, grey, inverted.

Write the file in only this plain-text format, with nothing before or after it and no code fences, keeping the
headers exactly:

## no_internet, wifi_no_load
(25 messages, one per line)
## phone_not_ringing, notifications_missing
(25)
## no_internet, notifications_missing
(25)
## screen_too_dim, colours_wrong
(25)
## talkback_on, colours_wrong
(25)
```
