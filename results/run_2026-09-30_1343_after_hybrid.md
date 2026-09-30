# Run log — after_hybrid

- Produced by: `run_eval.py::main`
- Retrieval: `store.py::search`, chunks from `chunker.py::split_documents`
- Corpus: `city_guides` (index variant `default`)
- top-k: 5 · relevance cutoff: 0.57
- Runs per question: 3, caching off
- When: 2026-09-30 13:43

This table is one row per QUESTION. The run log your README asks for is
one row per CRITERION, so aggregate these into it — criterion 1 is how many
of your questions had the answer in the retrieved chunks, and so on.

| Question | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| When does the concert season run in Thornby Wells? | pass | pass | pass |
| Is there anywhere to stay in Givens Mill? | pass | pass | pass |
| Is Halden Bay open during winter? | pass | pass | pass |
| Is Corry Vale difficult to navigate for someone with limited mobility? | pass | pass | pass |
| How long does it take to see the museum in Brightwater? | pass | pass | pass |

---

## The relevance gate on out-of-corpus questions

Produced by `run_eval.py::check_out_of_scope`, cutoff 0.57. Refused 5 of 5.

Retrieval is deterministic and the gate is a comparison against a
fixed number, so these do not vary between runs — one pass over the
list is the whole measurement.

| Out-of-scope question | Best distance | Gate |
|---|---|---|
| What is the capital of Mongolia? | 0.808 | refused |
| How do I change the oil in a diesel engine? | 0.883 | refused |
| Who won the 1994 World Cup? | 0.982 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.834 | refused |
| How do I write a for loop in Rust? | 0.854 | refused |

---

## Real output

This is what the system actually produced. Paste the relevant parts
into your README underneath the table — the rubric asks for real
output as text, not a description of it.

### When does the concert season run in Thornby Wells? — run 1

- Best distance: 0.2253 (passed the gate)
- Sources retrieved: guide_thornby_wells.md

```
The concert season in Thornby Wells runs from September to April (guide_thornby_wells.md).
```

### When does the concert season run in Thornby Wells? — run 2

- Best distance: 0.2253 (passed the gate)
- Sources retrieved: guide_thornby_wells.md

```
The concert season in Thornby Wells runs from September to April (guide_thornby_wells.md).
```

### When does the concert season run in Thornby Wells? — run 3

- Best distance: 0.2253 (passed the gate)
- Sources retrieved: guide_thornby_wells.md

```
The concert season in Thornby Wells runs from September to April (guide_thornby_wells.md).
```

### Is there anywhere to stay in Givens Mill? — run 1

- Best distance: 0.2717 (passed the gate)
- Sources retrieved: guide_givens_mill.md

```
No, there is nowhere to stay in the village itself; the nearest rooms are in Brightwater. 

Source: `guide_givens_mill.md`
```

### Is there anywhere to stay in Givens Mill? — run 2

- Best distance: 0.2717 (passed the gate)
- Sources retrieved: guide_givens_mill.md

```
No, there is nowhere to stay in the village itself; the nearest rooms are in Brightwater. (Source: `guide_givens_mill.md`)
```

### Is there anywhere to stay in Givens Mill? — run 3

- Best distance: 0.2717 (passed the gate)
- Sources retrieved: guide_givens_mill.md

```
Based on the provided documents, there is nothing to stay in within the village of Givens Mill itself; the nearest rooms are located in Brightwater (guide_givens_mill.md).
```

### Is Halden Bay open during winter? — run 1

- Best distance: 0.3008 (passed the gate)
- Sources retrieved: guide_halden_bay.md, guide_regional_transport.md, guide_seasons.md

```
Halden Bay is largely closed in the winter (`guide_seasons.md` and `guide_halden_bay.md`).
```

### Is Halden Bay open during winter? — run 2

- Best distance: 0.3008 (passed the gate)
- Sources retrieved: guide_halden_bay.md, guide_regional_transport.md, guide_seasons.md

```
Halden Bay is largely closed during the winter. 

This information comes from *guide_seasons.md* and *guide_halden_bay.md*.
```

### Is Halden Bay open during winter? — run 3

- Best distance: 0.3008 (passed the gate)
- Sources retrieved: guide_halden_bay.md, guide_regional_transport.md, guide_seasons.md

```
Halden Bay is largely closed in the winter (`guide_seasons.md` and `guide_halden_bay.md`).
```

### Is Corry Vale difficult to navigate for someone with limited mobility? — run 1

- Best distance: 0.4197 (passed the gate)
- Sources retrieved: guide_accessibility.md, guide_corry_vale.md

```
Yes, getting around the region with limited mobility is described as "Difficult" (from guide_accessibility.md). Specifically regarding Corry Vale, it has no public transport, villages are two to four miles apart, and there are footpaths rather than pavements (from guide_accessibility.md). Additionally, mobile coverage is genuinely absent in parts of Corry Vale (from guide_accessibility.md), and nothing within the valley is walkable from anything else with only one taxi that must be booked a day ahead (from guide_corry_vale.md).
```

### Is Corry Vale difficult to navigate for someone with limited mobility? — run 2

- Best distance: 0.4197 (passed the gate)
- Sources retrieved: guide_accessibility.md, guide_corry_vale.md

```
Yes, Corry Vale is difficult for someone with limited mobility because it has no public transport, villages are two to four miles apart, and there are footpaths rather than pavements (guide_accessibility.md). Additionally, mobile coverage is genuinely absent in parts of Corry Vale (guide_accessibility.md), and nothing within the valley is walkable from anything else, with only one taxi that must be booked a day ahead (guide_corry_vale.md).
```

### Is Corry Vale difficult to navigate for someone with limited mobility? — run 3

- Best distance: 0.4197 (passed the gate)
- Sources retrieved: guide_accessibility.md, guide_corry_vale.md

```
Yes, Corry Vale is difficult to navigate for someone with limited mobility because it has no public transport, villages that are two to four miles apart, and footpaths rather than pavements (guide_accessibility.md). Additionally, nothing within the valley is walkable from anything else, there is only one taxi in the entire valley which must be booked a day ahead, and mobile coverage is genuinely absent in parts of Corry Vale (guide_corry_vale.md and guide_accessibility.md). 

Sources: `guide_accessibility.md` and `guide_corry_vale.md`
```

### How long does it take to see the museum in Brightwater? — run 1

- Best distance: 0.2902 (passed the gate)
- Sources retrieved: guide_accessibility.md, guide_brightwater.md, guide_givens_mill.md, guide_marchwood.md

```
Based on the provided documents, you should allow 90 minutes to see the mill building museum in Brightwater (*guide_brightwater.md*).
```

### How long does it take to see the museum in Brightwater? — run 2

- Best distance: 0.2902 (passed the gate)
- Sources retrieved: guide_accessibility.md, guide_brightwater.md, guide_givens_mill.md, guide_marchwood.md

```
Based on `guide_brightwater.md`, you should allow 90 minutes for the mill building museum in Brightwater.
```

### How long does it take to see the museum in Brightwater? — run 3

- Best distance: 0.2902 (passed the gate)
- Sources retrieved: guide_accessibility.md, guide_brightwater.md, guide_givens_mill.md, guide_marchwood.md

```
You should allow 90 minutes to see the mill building museum in Brightwater (guide_brightwater.md).
```
