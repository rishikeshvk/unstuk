# Failure codes

Every clear test line the shipped int8 graph gets wrong, with one cause each, for the M9 write-up's failure
analysis. The causes were fixed in the [M9 spec](../../docs/m9-spec.md), section 4, before any mistake was read.

`test-int8.jsonl`: one line per mistake, `{"id", "cause", "note"}`. `id` is a test line's id, `cause` one of the
spec's list, and `note` says in a few words what tipped it. `failures.load_failures` refuses the file unless it codes
each mistake of the int8 graph once, so it must be redone if the shipped graph changes.

Precedence, when two causes fit:

1. `held_out`: a line of a held-out intent is coded so, whatever else is true of it, since the model never
   trained on that intent.
2. `debatable_label` before the others: if the label itself is open, the model's pick may not be a mistake.
3. `collision` before `lexical_pull`: a line whose topic isn't the phone, or is told as a story about something
   else, is a collision even when one word also points to a setting.
4. `wording` before `lexical_pull`: when a typo or an unusual word for the setting ("the glass", "microscopic")
   hides it, the line is coded `wording`, even if the model then followed another word.

Coded by Claude from the test lines and the graph's probabilities, and reviewed by the developer. Only proxy test
lines are coded here, which LLMs wrote; real messages are never read or quoted (M8 spec, section 3).
