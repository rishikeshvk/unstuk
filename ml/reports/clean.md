# Cleaning report

Written by `uv run unstuk-clean`; do not edit by hand.

## Stages

| Stage | Lines left |
| --- | --- |
| raw pool | 7090 |
| after review decisions | 7090 |
| after exact duplicates | 7041 |
| after near duplicates (same label, 0.9) | 6983 |
| after test leakage (0.8) and guide examples | 6928 |

## Dropped, by reason

| Reason | Lines |
| --- | --- |
| near duplicate | 58 |
| close to the test set | 52 |
| exact duplicate | 49 |
| a labelling-guide example | 3 |

## Closeness to the test set

Training lines at or above each character-n-gram cosine similarity to some test line:

| Threshold | Lines |
| --- | --- |
| 0.7 | 137 |
| 0.8 | 52 |
| 0.9 | 14 |

Closest pairs (training line, test line, similarity):

- `who won the cricket match yesterday` / `Who won the cricket match yesterday` (1.00)
- `no sound` / `no sound` (1.00)
- `Thank you very much` / `Thank you very much` (1.00)
- `Hello, how are you` / `Hello, how are you` (1.00)
- `Screen goes off too quickly` / `My screen goes off too quickly` (1.00)
- `phone keeps restarting itself` / `My phone keeps restarting by itself` (0.97)
- `how I make my screen brighter?` / `How can I make my phone screen brighter?` (0.94)
- `how to make screen stay on longer?` / `How do I make the screen stay on for longer?` (0.94)

## Flagged labels

0 lines go to `data/clean/review.jsonl`.

| Given | Model says | Lines |
| --- | --- | --- |

## Shortcut check

| Label | Lines | Mean words | Most common first words |
| --- | --- | --- | --- |
| app_permission | 426 | 15.5 | the 11%, why 10%, my 9%, i 8%, how 7% |
| bluetooth_earphones | 424 | 14.5 | my 25%, i 14%, the 12%, how 10%, why 8% |
| colours_wrong | 423 | 15.2 | my 17%, the 14%, why 9%, i 8%, how 8% |
| no_internet | 480 | 19.5 | i 17%, my 11%, how 8%, why 7%, the 4% |
| notifications_missing | 451 | 16.7 | my 19%, i 9%, how 9%, why 8%, the 8% |
| out_of_scope | 1717 | 15.6 | my 15%, i 12%, can 8%, the 6%, how 6% |
| phone_not_ringing | 451 | 17.9 | my 18%, i 12%, phone 8%, how 7%, the 6% |
| reset_network | 439 | 16.5 | i 15%, how 13%, my 13%, can 12%, please 8% |
| screen_too_dim | 442 | 15.4 | my 13%, i 12%, the 11%, screen 9%, why 9% |
| screen_turns_off_fast | 415 | 15.9 | screen 11%, the 11%, i 11%, my 10%, why 9% |
| talkback_on | 420 | 17.5 | i 19%, my 13%, why 8%, phone 8%, how 8% |
| text_too_small | 409 | 14.2 | the 18%, my 12%, i 11%, how 9%, why 7% |
| wifi_no_load | 431 | 18.6 | wifi 11%, the 10%, my 9%, why 7%, how 7% |

Tokens in 15+ lines with 90%+ of them under one label:

| Label | Tokens |
| --- | --- |
| app_permission | microphone (62), allow (60), access (36), mic (24), uber (22) |
| bluetooth_earphones | wireless (71), pair (36), pairing (22), searching (19), disconnected (15) |
| colours_wrong | colours (115), negative (43), colors (42), faces (34), inverted (22), opposite (16), film (15) |
| no_internet | aeroplane (24) |
| notifications_missing | alerts (55), notifications (45), until (43), hours (36), alert (20) |
| out_of_scope | flashlight (112), number (79), contact (60), subject (59), body (50), com (49), ' (31), tanaka (28), q (23), zoomed (22), review (21), named (20), jp (20), hi (20), keys (20), best (20), thanks (19), fell (18), kenji (18), sharma (17), 'hi (16), cracked (15), hot (15), add (15), petrova (15), tomorrow (15) |
| phone_not_ringing | missed (133), moon (28), rang (26), heard (22) |
| reset_network | saved (29), connections (27) |
| screen_too_dim | dim (83), dull (47), brighter (38), sun (38), darker (34) |
| screen_turns_off_fast | seconds (87), longer (55), locks (45), timeout (35), short (30), locking (18) |
| talkback_on | tap (135), scroll (45), double (39), talkback (38), speaking (34), whatever (25), talks (25), word (15) |
| text_too_small | bigger (124), writing (94), words (90), tiny (89), font (59), larger (29), print (18) |
| wifi_no_load | tick (47), pages (40), joined (32), conected (31), router (28), mark (19) |

## Splits

| Label | Train | Dev |
| --- | --- | --- |
| app_permission | 363 | 63 |
| bluetooth_earphones | 361 | 63 |
| colours_wrong | 360 | 63 |
| no_internet | 408 | 72 |
| notifications_missing | 383 | 68 |
| out_of_scope | 1395 | 322 |
| phone_not_ringing | 386 | 65 |
| reset_network | 373 | 66 |
| screen_too_dim | 376 | 66 |
| screen_turns_off_fast | 354 | 61 |
| talkback_on | 358 | 62 |
| text_too_small | 349 | 60 |
| wifi_no_load | 367 | 64 |
| **total** | 5833 | 1095 |

| Source | Train | Dev |
| --- | --- | --- |
| generated | 5480 | 1045 |
| mobile_actions | 241 | 50 |
| seed | 112 | 0 |
