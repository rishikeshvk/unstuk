# M9 in plain words: the whole story, in one place

2026-10-08 · Summary of the ninth phase. The write-up itself is [writeup.md](writeup.md).

## The question we set out to answer

Eight phases left the story spread over a dozen documents, with tables and no pictures. M9 asked: what did it take
to put a small AI model on a phone that fixes settings by itself, and where does it still go wrong? The answer
had to fit in one document a stranger can read in ten minutes.

## What we made

- **Five figures,** drawn by code from the same scores the earlier reports used:
  - where the app's size goes;
  - every approach we tried, side by side;
  - how honest each one's confidence is;
  - what the app does with each test message;
  - why the model's mistakes happen.
  The code refuses to draw anything unless its numbers match the published ones exactly.
- **Four screenshots from the Moto:** a fix done and checked, a fix that asks first, a "which do you mean?" and a
  polite "I can't help with that".
- **A look at every mistake.** The model gets 57 of the 574 clear test messages wrong. We gave each one a reason,
  from a list of reasons written down before we looked.
- **A new front page** for the project that leads with the write-up.

## What we found

- **The biggest group of mistakes is the three problems the model never trained on.** It often turns them away as
  "not something I can help with", because they're unfamiliar.
- **Next comes a word that points the wrong way.** "Calls ring normally, but my WhatsApp messages come silently"
  is read as a ringing problem, because of the word "ring".
- **Most mistakes are caught before they do harm.** Of the 57, the app would have changed a setting by itself on
  17. The rest it would ask about, check with the person first, or turn away.
- **One chatbot's messages caused most mistakes.** Gemini wrote less than half the test, but 40 of the 57
  mistakes are in its messages. It uses unusual words, like "the glass" for the screen. Our training examples came
  from one kind of writer, which is why messages from real people matter so much.
- **The model passes five of the six bars we set before building it.** It misses the one for problems it was
  never taught.

## Things we learned

- **Some old results can't be rebuilt.** Two earlier models' files were no longer on the computer, so they stay
  in the tables but not in the pictures. Keeping the checked fingerprint of every model file is what made that
  clear, instead of a quiet mismatch.
- **The phone isn't the laptop, even for picking an example.** Two complaints chosen on the laptop to show
  particular replies got different replies on the phone, because the phone also tells the model what its settings
  are. The screenshots use complaints checked on the phone.
- **A chart is checked like code.** Each figure was drawn, looked at and fixed (cut-off dots, misleading tick
  marks) before it went in.

## What's still open

The real messages from M8. When they are in, the write-up gets one more section, and then the messages are deleted.
