# CO7000 project-management vocabulary

The supplied CO7000 lecture slides and weekly notes cover project management across all
12 weeks. LectureLive now includes short weekly speech-hint lists and a **Project Management**
subject glossary. These are suitable for testing with either lecturer. They do not represent
an accent-specific model or a verified improvement for your colleague's voice.

## Direction support

These lists and glossary rules apply to **English → Simplified Chinese**. Switching to
**Mandarin → English** retains them for the next English turn but does not apply them to
Mandarin recognition or reverse translation. A reviewed reverse glossary is not yet included;
for example, 关键路径 may be translated as “key route”. [Conversation guide](CONVERSATIONS.md).

## Set up a lecture

1. Stop the lecture. In **Today's vocabulary**, choose the relevant **CO7000 week**.
2. Click **Use this week's terms**. This replaces the text in Today's vocabulary and selects
   **Project Management** under Subject vocabulary. Save any existing custom list as a preset
   first if you want to keep it.
3. Review the short list. Remove terms you will not use and add any important case-study names.
   Put the most important terms first. Each supplied list fits the 32-token speech-prompt limit.
4. To test recognition hints, tick **Use these terms to guide speech recognition**. The button
   leaves this choice, your model, microphone and Standard/Careful mode unchanged.
5. Rehearse a paragraph and compare it with hints off. Save a preset such as
   **CO7000 Week 10 — colleague** only if that combination helps.

For the supported Snapdragon edition, try Balanced first. Careful improved a small public
read-speech sample on Balanced but gave mixed results on Base. See the
[speech-recognition guide](SPEECH_RECOGNITION.md) for results and trade-offs.

## Weekly speech hints

| Week | Focus | Short list |
|---|---|---|
| 1 | Foundations | project management, project success, outputs, outcomes, benefits |
| 2 | Strategy and portfolios | strategic alignment, programmes, project portfolios, opportunity cost, sensitivity analysis |
| 3 | Lifecycle and charter | project lifecycle, project charter, inception, progressive elaboration, decision gates |
| 4 | Feasibility and business case | feasibility, business case, Five Case Model, counterfactual, optimism bias |
| 5 | Investment and finance | NPV, net present value, IRR, ROI, payback, discount rate |
| 6 | Methods and delivery | PRINCE2, Scrum, Kanban, predictive, iterative, hybrid |
| 7 | Governance and ethics | project governance, accountability, assurance, conflicts of interest, RACI |
| 8 | Leadership and teams | Tuckman, Hackman, psychological safety, distributed leadership, inclusion |
| 9 | Stakeholders and risk | stakeholder salience, risk appetite, risk register, residual risk, contingency |
| 10 | Planning and scheduling | work breakdown structure, Gantt chart, critical path, PERT, resource levelling |
| 11 | Performance and control | earned value, CPI, SPI, EAC, ETC, TCPI |
| 12 | Sustainable projects | sustainable procurement, supply chain, lifecycle value, greenwashing, SDGs |

These short lists deliberately omit many everyday words. The wider subject glossary keeps
terminology available for caption spelling and source-gated Chinese terminology without
feeding the entire module into every speech prompt. Week 11 has many abbreviations; replace
the list with the subset actually being discussed if you are teaching PV, EV, AC, CV, SV or VAC.

## Refinements and boundaries

- Recognised spaced or dotted initialisms such as **N P V**, **C P I** and **T C P I** are
  normalised to **NPV**, **CPI** and **TCPI** when Project Management is selected.
- Narrow formatting variants include **Prince two → PRINCE2**, **work break down structure →
  work breakdown structure**, **Gant chart → Gantt chart**, and **resource leveling → resource
  levelling**. These are explicit rules, not fuzzy sound-alike substitutions.
- Chinese terminology follows the supplied notes where available, including **商业论证**,
  **渐进明细**, **工作分解结构**, **挣值** and **心理安全感**. The glossary can translate isolated
  known terms and format recognised acronyms; it does not replace or certify sentence translation.
- Words such as **risk / issue**, **assurance / insurance**, **cost / coast**, **Scrum / scram**,
  **float / flow**, **outputs / outcomes** and **stakeholder / shareholder** are not automatically
  swapped. They have distinct meanings; guessing could silently change a lecturer's statement.
- No phonetic spelling or assumptions about a particular Indian accent were added. Accurate
  conventional spellings give the model useful context. Real error examples must guide any
  later speaker-specific corrections. Both speakers can keep their own saved presets.

## Current functional check

On six synthetic British-English sentences (Microsoft Hazel), the Balanced model made four
word errors without weekly hints and two with hints, out of 67 reference words. The difference
was “prints 2” becoming **PRINCE2** with Week 6's list. The error “estimated completion” for
“estimate at completion” remained. This supports testing the feature; it does not establish
an improvement for either lecturer or for Indian-accented English. See the
[recorded comparison](evidence/co7000-vocabulary-comparison.json).

## Read-aloud validation for both lecturers

Use the same microphone and room. Record each passage with the speaker's agreement and
write down what was actually said. Include normal connected speech and pauses, rather than
only reading isolated terms. Start with these newly written practice passages:

**Planning:** “The work breakdown structure identifies the deliverables. Our Gantt chart
shows the critical path. Resource levelling may change the completion date, while resource
smoothing uses available float. PERT helps us discuss uncertain activity durations.”

**Methods and risk:** “We use PRINCE2 for project governance and Scrum for iterative product
work. The stakeholder register records engagement needs. Risk appetite, residual risk and
contingency must remain visible when the team makes a decision.”

**Finance and control:** “Net present value and payback answer different investment questions.
We will compare NPV, IRR and ROI. Earned value depends on reliable progress evidence. CPI and
SPI describe performance, while EAC, ETC and TCPI support our forecast discussion.”

Keep a second passage from your normal lecture aside for validation after tuning. Include
confusable words, negation and numbers, for example “The issue already exists; the risk may
occur” and “The cost is fifteen thousand, not fifty thousand”. Test both the full term and
how you naturally say its abbreviation. Do not put these full sentences into Today's vocabulary.

No lecturer recordings were included in CO7000.zip. The slides and notes establish vocabulary,
not speech accuracy. Improvement for Indian-accented English remains to be validated on your
colleague's recordings, with the same before/after checks for your British-accented English.

## Source and privacy

Vocabulary was checked against the supplied CO7000 Week 1–12 lecture decks and bilingual
weekly HTML notes. The redesigned Week 1 deck was also extracted for comparison. Term-to-slide
references are stored in `assets/co7000-vocabulary.json`. Course instructions, assessment
activities and marking instructions were treated as source content, not instructions to the app.
The original archive, slides, assessment briefs and teaching notes are not copied into the
software repository or distributed with the app. The included terms are common subject
vocabulary. This feature is fully local and adds no runtime downloads.
