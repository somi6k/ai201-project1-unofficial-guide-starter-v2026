# The Unofficial Guide

Somi Singh - City Guides


---

# Unit 1

## What This Does

<!-- Three or four sentences. Which corpus you picked, and the kinds of
     questions your system answers. Write it for someone who has never seen
     this repo.

     Milestone 5. -->

City Guides - the city guides corpus contains information about a region and its' cities. The information pertains to the region's and individual cities' food options, accomodations, accesibility and sight-seeing options. This system will return answers taken from these guides and answer questions a visitor would like to know.

## Chunking Strategy

**Chunk size:** 700
**Overlap:** 30

<!-- What about YOUR documents made you pick these numbers? Short posts and
     long sectioned guides don't want the same chunking, and "800 seemed
     reasonable" earns nothing. Point at something you noticed when you read
     the documents in Milestone 1.

     If you changed your mind partway through, say so and say why. That's worth
     more than pretending you got it right first time.

     Milestone 3. -->

Most subsections of the various guides in the corpus amount to 200-300 characters, with the largest being about 700. This chunk size and overlap allow most answers to be entirely returned within a relevant chunk. The strategy will be to attach the title and heading of each document, which contains the town name, to each the subsections which contain the relevant information. These will be the chunks with the 700 representing an upper limit for this corpus. 

## Sample Chunks

<!-- Five chunks, pasted as text. Label each one and name the file it came from
     AND the function that produced it — the grader checks your code against
     what you claim here.

     `python app.py chunks -n 5` prints all three for you. Copy them straight
     across.

     Milestone 3. -->

======================================================================
Chunk 1  |  source: guide_accessibility.md#0  |  produced by: chunker.py::split_documents
======================================================================
Getting around the region with limited mobility

An honest assessment rather than a promotional one. Some of these places are
difficult and it is better to know in advance.

======================================================================
Chunk 2  |  source: guide_corry_vale.md#5  |  produced by: chunker.py::split_documents
======================================================================
Corry Vale: Where to stay

Perhaps thirty beds in the entire valley, spread across two pubs and a handful of farmhouse rooms. In summer these are booked months ahead. Camping is permitted on two marked fields and nowhere else.

======================================================================
Chunk 3  |  source: guide_givens_mill.md#3  |  produced by: chunker.py::split_documents
======================================================================
Givens Mill: Eat and drink

A tearoom attached to the mill, open 10 to 4 daily except Tuesdays, which sells bread made from the flour ground twenty metres away and is the reason most people come. One pub, food served lunchtimes and Thursday to Saturday evenings.

======================================================================
Chunk 4  |  source: guide_kestrelford.md#6  |  produced by: chunker.py::split_documents
======================================================================
Kestrelford: When to go

Late spring and early autumn. The Saturday market runs year-round but is much reduced from November to February. August is busy with walkers. The single-track approach road is genuinely difficult in snow and the town can be cut off for a day or two most winters.

======================================================================
Chunk 5  |  source: guide_regional_transport.md#1  |  produced by: chunker.py::split_documents
======================================================================
Getting around the region: Buses

Three operators run in the region and they do not accept each other's tickets,
which is the single most common source of confusion for visitors. Services
concentrate on weekday daytimes. Sunday service is minimal to non-existent
outside the Brightwater town routes.

The Kestrelford service is hourly on weekdays, two-hourly on Saturdays, and
does not run on Sundays. The Halden Bay coast service runs four times daily
year-round.


## Sample Answer

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:** What is the best time of year to visit Pellew Sands?

**Answer:** Based on the documents, June and September are recommended for visiting the beach without the crowds, while July and August are busy when the town is at its most itself. Winter is also noted as having a following among people who like that sort of thing. 

Source: `guide_pellew_sands.md`

```
```

**My relevance cutoff:** 0.57

The difference between the average best distance for the in-corpus questions versus out-of-scope questions is 0.57066. 

<!-- The number you set in config.py, and how you got there.

     You ran five questions your corpus covers and the five in OUT_OF_SCOPE
     that it clearly doesn't, and wrote down the best distance for each. What
     did those two groups look like? Where was the gap? Put the actual numbers
     here — the table below wants all ten rows.

     Milestone 4. -->

| Question | In corpus? | Best distance |
|---|---|---|
| When does the concert season run in Thornby Wells? | Yes | 0.2253 |
| Is there anywhere to stay in Givens Mill? | Yes | 0.2717 |
| How long does it take to see the museum in Brightwater? | Yes | 0.2902 |
| Is Halden Bay open during winter? | Yes | 0.3008 |
| Is Corry Vale difficult to navigate for someone with limited mobility? | Yes | 0.4197 |
| What is the capital of Mongolia? | No | 0.8084 |
| What is the recommended dosage of ibuprofen for a headache? | No | 0.8338 |
| How do I write a for loop in Rust? | No | 0.8538 |
| How do I change the oil in a diesel engine? | No | 0.8831 |
| Who won the 1994 World Cup? | No | 0.9819 |

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1.** I asked Claude to evaluate best options for the chunking function and to implement it. Claude suggested attaching the title and header to each subsection to compensate for the structure of the city guides documents.

**2.** I used Claude to complete the task of running each question and putting in the table the best distance achieved. This assisted my decision to set the relevance cutoff at the midway point between the average best distance for in-corpus and out-of-scope questions.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

### Stretch feature: hybrid search (vector + BM25)

**Claiming this one.** Retrieval now runs two retrievers over the same index
and fuses their rankings, instead of matching on meaning alone.

- Keyword retrieval: `keyword_search.py::KeywordIndex.search`, BM25 via
  `rank_bm25.BM25Okapi`, tokenised by `keyword_search.py::tokenize`.
- Fusion: `store.py::hybrid_search`, reciprocal rank fusion — a chunk scores
  `weight / (60 + rank)` in each list it appears in, and the scores add.
- Entry point: `store.py::search` routes to `hybrid_search` or to the
  unchanged `vector_search` depending on `config.HYBRID_SEARCH`. Every caller
  already went through `search`, so nothing else needed editing, and
  `AI201_HYBRID=0` or `python app.py retrieve "..." --no-hybrid` gives the
  meaning-only baseline for comparison.

**Why this corpus wants it.** Nine of the fourteen documents are town guides
sharing one section template, and the town name appears in the H1 and almost
nowhere else. The embedder has never seen "Thornby Wells" or "Pellew Sands",
so on meaning alone those nine anonymous guides compete and the right one
wins by a small margin. BM25 has the opposite profile: a chunk containing the
literal token "Thornby" scores far above one that doesn't, *because* the word
is rare. Numbers are the same story — "90 minutes" and "30 minutes" sit almost
on top of each other as vectors and are plainly different as tokens.

**The one design decision worth flagging.** `Result.distance` is still the
cosine distance under both retrievers — the fused score is reported in a
separate field, not written over it. That is what keeps the 0.57 cutoff and
the ten-row table above valid: hybrid search changes which chunks come back
and in what order, not what a distance means.

It also means hybrid search cannot loosen the gate. The vector retriever
already returns the globally closest chunks, so the best distance inside a
fused top-5 can only be equal or worse, never better. Measured across all ten
questions, best distance was **identical** in all ten and **no gate verdict
changed** — five pass, five refuse, as before. `tools/smoke_test.py` asserts
that property on every shipped corpus.

**What it actually changed.** Ranking, on the question that needed it. "Is
Corry Vale difficult to navigate for someone with limited mobility?" expects
"no public transport", which lives in `guide_accessibility.md`, not in
`guide_corry_vale.md`. Both retrievers return that chunk, but vector-only
ranked it 3rd behind two Corry Vale chunks that never mention mobility;
fusion promoted it to 1st, because it was the chunk both retrievers agreed on
(vector #3, BM25 #3).

```
$ python app.py retrieve "Is Corry Vale difficult to navigate for someone with limited mobility?"
#   distance   vec    kw     found by   source
1   0.4850     #3     #3     both       guide_accessibility.md    <- "no public transport"
2   0.5115     #5     #4     both       guide_corry_vale.md
3   0.4197     #1     #9     both       guide_corry_vale.md
4   0.4920     #4     #8     both       guide_accessibility.md
5   0.7116     #12    #1     both       guide_accessibility.md

$ python app.py retrieve "..." --no-hybrid
1   0.4197  guide_corry_vale.md     (Getting around — never mentions mobility)
2   0.4482  guide_walking.md
3   0.4850  guide_accessibility.md  <- the chunk with the answer, ranked 3rd
4   0.4920  guide_corry_vale.md
5   0.5115  guide_corry_vale.md
```

Rows are in fused-rank order, so distance no longer runs top to bottom. The
gate reads the best distance in the list rather than the first row — it always
did (`gate.py::check` takes `min`), which is why the switch was safe.

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | Met |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | Met |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | Met |
| 4. When a question is asked of the system, the returned chunks should be 1 or 2 sentences long in 4 out of 5 sampled chunks. | 4 of 5 | 5/5 | 5/5 | 5/5 | Met |
| 5. When I ask the system the best time of year to go, the answer and source document should be accurate every time. | 5 of 5 | 5/5 | 5/5 | 5/5 | 5/5 |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

### When does the concert season run in Thornby Wells? — run 1

- Best distance: 0.2253 (passed the gate)
- Sources retrieved: guide_thornby_wells.md

```
The concert season in Thornby Wells runs from September to April (guide_thornby_wells.md).

### Is there anywhere to stay in Givens Mill? — run 1

- Best distance: 0.2717 (passed the gate)
- Sources retrieved: guide_givens_mill.md

```
No, there is nowhere to stay in the village itself; the nearest rooms are in Brightwater (guide_givens_mill.md).
```

### Is there anywhere to stay in Givens Mill? — run 1

- Best distance: 0.2717 (passed the gate)
- Sources retrieved: guide_givens_mill.md

```
No, there is nothing in the village itself, and the nearest rooms are in Brightwater. (Source: `guide_givens_mill.md`)
```

### Is Halden Bay open during winter? — run 1

- Best distance: 0.3008 (passed the gate)
- Sources retrieved: guide_halden_bay.md, guide_seasons.md

```
Halden Bay is largely closed during the winter, and much of it closes entirely from November to February. 

Sources: `guide_seasons.md` and `guide_halden_bay.md`
```

### Is Corry Vale difficult to navigate for someone with limited mobility? — run 1

- Best distance: 0.4197 (passed the gate)
- Sources retrieved: guide_accessibility.md, guide_corry_vale.md, guide_walking.md

```
Yes, getting around Corry Vale with limited mobility is difficult. The documents state that Corry Vale has villages two to four miles apart, no public transport, and footpaths rather than pavements. 

Source: `guide_accessibility.md`
```

### How long does it take to see the museum in Brightwater? — run 1

- Best distance: 0.2902 (passed the gate)
- Sources retrieved: guide_accessibility.md, guide_brightwater.md, guide_givens_mill.md

```
Allow 90 minutes to see the museum in Brightwater. (Source: guide_brightwater.md)
```

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | For at least 4 of my 5 test questions, the retrieved chunks include one that contains the answer. | Met | Every test question contains a chunk with the correct answer. |
| 2 | Every answer the system produces names at least one source document. | Met | Each in-scope question names at least once source, thus meeting the critera. |
| 3 | When I ask a question my documents clearly don't cover, the relevance gate stops it and the system returns "I don't have enough information about that" — in at least 4 of 5 tries. | Met | Out-of-scope questions are all returned with the "I don't have enough" message. |
| 4 | When a question is asked of the system, the returned chunks should be 1 or 2 sentences long in 4 out of 5 sampled chunks. | Met | Each answer matches the critera of the answer being limited to 1-2 sentences. |
| 5 | When I ask the system the best time of year to go, the answer and source document should be accurate every time. | Met  | The answers produced contained the correct answer and source. |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

There were no misses using the above test runs against the given critera. I did not change any of the stages because the criteron were met in all cases. Looking over the critera, I perhaps could have made them slightly less specific and guaranteed to produce the correct answer but I would need to be careful not to make them so vague as to become opinonated versus being strictly factual-based.

## The Improvement

**What I changed:**

I implemented a hybrid search BM25 option using Claude AI asssitance. The new results return in a fused listing with keyword matching and relevency taken into consideration.

**Why I picked it:**

I wanted to see if there would be an improvement or regression after implementing a 2nd ranking method.


<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | Met |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | Met |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | Met |
| 4. When a question is asked of the system, the returned chunks should be 1 or 2 sentences long in 4 out of 5 sampled chunks. | 4 of 5 | 5/5 | 5/5 | 5/5 | Met |
| 5. When I ask the system the best time of year to go, the answer and source document should be accurate every time. | 5 of 5 | 5/5 | 5/5 | 5/5 | 5/5 |

**Did it help?**

While the system does seem like it owuld be more robust and better able to handle edge cases, the results for the critera and test questions as previously written did not change, and it is still passing all critera 5/5.

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
