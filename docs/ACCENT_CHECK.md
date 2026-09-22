# A short speech check with your colleague

Use this before changing settings for Indian-accented English, or any speaker
whose words are being missed. It takes about five minutes with both lecturers.
An accent is not a single voice: use the colleague's own normal speaking style.

## 1. Make a fair comparison

1. Use the microphone and speaking distance planned for the lecture. Click
   **Test microphone** and resolve quiet input or clipping first.
2. Select **English → Simplified Chinese** while checking English words. This
   separates recognition errors from Auto's language decisions.
3. Start with **Standard**, with **Use these terms to guide speech recognition**
   unticked. Save this as your baseline preset.
4. Read one short passage, then save the transcript. Note the actual mistakes,
   particularly technical terms, names, numbers and words such as **not**.
5. Change just one setting while stopped and repeat the same passage. Use
   **Balanced / Whisper Small** where available, then compare Standard with
   Careful. Careful can take longer and can also make some words worse.
6. Choose the relevant **Subject vocabulary**. For CO7000, choose the week and
   click **Use this week's terms**. Compare hints off and on separately. Include
   only the few terms used in that passage, in their normal spelling.

The saved English caption can include glossary spelling corrections; the
developer benchmark reports raw Whisper words. Judge the captions your class
will actually see, as well as the raw recognition when diagnosing a problem.

## 2. Use the same words for both lecturers

Here are newly written examples. Read each numbered item as a separate short
turn. Do not paste these sentences into Today's vocabulary.

1. “The work breakdown structure identifies our deliverables. The Gantt chart
   shows dependencies, and the critical path determines the completion date.”
2. “A risk may happen in the future. An issue already exists. We record the
   residual risk and our contingency in the risk register.”
3. “We use PRINCE2 for governance and Scrum for iterative delivery. The project
   sponsor reviews the business case at each decision gate.”
4. “The estimate is fifteen thousand pounds, not fifty thousand. A positive net
   present value does not guarantee that the project will succeed.”
5. “The ESP32 runs FreeRTOS. The interrupt service routine handles the sensor,
   and the MOSFET switches the motor.”

Use the appropriate CO7000 weekly list or a short custom list for each item;
do not combine every week's terms into one prompt. Say abbreviations as you
normally would in class. Record the actual spoken form in any reference transcript.

## 3. Confirm it helps on something new

Save the best combination as a preset for your colleague. Keep your own working
preset. Then ask each lecturer to explain a different slide naturally for about
one minute, including a number, a negative statement and several technical terms.
Check the words and caption delay. A correction on the practice passage alone
does not establish that a setting is better for an entire lecture.

Finally try a brief English/Mandarin conversation with Auto, then a five-minute
rehearsal with the real microphone and projector. An Auto “Language unclear” turn
is a missed turn, not a correctly recognised sentence. Switch to manual English
and repeat if necessary. Background noise tests in software do not replace this.

## What would help us improve recognition further?

With each speaker's agreement, keep 2–5 minutes of their normal speech plus an
accurate transcript, including the words that went wrong. Use the same passage
for both lecturers and also keep a separate, unpractised passage for validation.
Record the microphone, room, speaking distance, computer, model/profile,
Standard/Careful setting and vocabulary list. Reference transcripts must describe
what was actually said, including any deviations from the written passage.

LectureLive saves text; it does not record microphone audio. If you make an
audio recording separately, keep it local unless the speaker agrees to share it.
Do not include students' voices without their agreement. Developers can evaluate
mono 16 kHz PCM16 WAV clips of at most 30 seconds using
[the offline evaluator](SPEECH_RECOGNITION.md#developer-evaluation). Longer speech
must be split with matching reference text. Keep private files and reports under
`tests/artifacts`; never commit them to the public repository.

[Recognition options and measured results](SPEECH_RECOGNITION.md) ·
[CO7000 terms](CO7000_VOCABULARY.md)
