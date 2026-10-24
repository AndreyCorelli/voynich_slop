# Latin inventory acceptance and candidate scale

The generated inventories retain useful word-level specificity against the two
frozen spelling-control families, but are far too large for a naive flat solver
membership expansion. Three tests and four-row validation pass; no Z3 runs.

| Inventory | Real query types accepted / 3,406 | Changed anagrams accepted / 3,398, across seeds | Uniform strings accepted / 3,406, across seeds |
|---|---:|---|---|
| Default morphology | 2,851 | 48 / 51 / 49 | 10 / 8 / 7 |
| Default plus attested | 3,034 | 52 / 58 / 51 | 12 / 9 / 7 |
| Broader morphology | 3,261 | 62 / 69 / 62 | 11 / 9 / 9 |
| Broader plus attested | 3,289 | 65 / 75 / 64 | 13 / 10 / 9 |

Columns list independent fixed seeds 4701,4702,4703. Broader morphology alone
accepts 1.82–2.03% of changed anagrams and 0.26–0.32% of uniform strings. Broader
plus-attested accepts 1.88–2.21% and 0.26–0.38%, respectively. These are descriptive
sample acceptance rates, not population false-positive probabilities. Some
controls may be genuine Latin words; none is labeled inherently impossible.

Across the unchanged 9,432 tokens in eligible later-source blocks, real membership
coverage is 8,512 default, 8,979 default-plus-attested, 9,252 broader, and 9,300
broader-plus-attested. Control acceptance is also saved with token weighting,
separate from type counts; repetitions must not be counted as independent trials.

## Public candidate scale

| Inventory | Fixed-two fixture, candidate occurrences across 24 words | Mixed-1/2/3 fixture |
|---|---:|---:|
| Default morphology | 30,390,429 | 39,142,423 |
| Default plus attested | 30,501,586 | 39,253,848 |
| Broader morphology | 68,059,210 | 92,346,014 |
| Broader plus attested | 68,110,880 | 92,397,410 |

Per-word maximum candidate count is about 2.51 million default and 6.23 million
broader. Counts include only inventory entries whose length could encode the
observed ciphertext word under L1–3: ceil(cipher length/3) through cipher length,
clamped to the inventory's public maximum length. They count membership
candidates repeatedly across words, not distinct words or exact SMT constraints.
They precede structural/prefix pruning and are not solver timing measurements.
True plaintext lengths and key mappings are not used for pruning. Large numbers
make flat enumeration an unsuitable immediate recovery run.

The fixed 24-word synthetic fixtures regenerate length observations using seed
4501 and both existing key profiles, in canonical i/u spelling. They differ from
the earlier u/v-preserving model. Ground truth constructs the fixtures only; the
candidate calculation receives observed ciphertext lengths, inventory histogram
and L1–3 bounds. The profile is not imposed as a recovery constraint.

## Frozen controls and limits

All 3,406 distinct canonicalized frozen query types get one uniform same-length
letter string and one changed within-type anagram per seed. The uniform alphabet
is the fixed canonical Latin alphabet. Uniform controls are not rejected for
accidental inventory membership. Anagrams use at most 100 draws solely to change
the spelling; eight unchangeable types remain explicitly unavailable. No collision,
length, inventory-membership or score-based rejection is allowed. The same controls
are reused across every inventory variant. Generating code/data and seeds are
frozen before scoring. Some generated controls can coincide with real query types.

These are spelling membership controls, not encrypted synthetic texts or shuffled
ciphertext controls. A cipher solver searches many keys and word assignments; it
can amplify accidental compatibility despite low per-string acceptance. This
experiment cannot estimate that amplification, choose a manuscript language or
prove reliable key recovery. Inventories and controls share canonical i/u spelling
and inherit the morphology resource's known analysis/filter limitations.

```sh
.venv/bin/python -m benchmarks.latin_inventory_calibration --run
.venv/bin/python -m benchmarks.latin_inventory_calibration --validate
```

Artifacts: `experiments/results/latin-inventory-calibration/` saves protocol,
source/inventory/code hashes, frozen controls including unavailable cases,
per-control accepted pairs and counts, type/token weighting, inventory length
histograms, per-observation candidate counts and validation. Validation regenerates
controls, checks invariants, rehashes inventories and reconstructs every score.
Tests cover deterministic draws, unavailable controls, public length arithmetic
and separation of type/token weighting.

The next justified step is a compact lexicon/morphology representation, calibrated
against independently generated forms before full recovery. Further long flat
solver runs or target-word shortlists would not address the measured scale issue.
