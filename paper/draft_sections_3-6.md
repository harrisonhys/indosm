# Draft — Sections 3–6

> Working draft, 28 Oct 2026. Numbers come from `HYBRID.md`, `SUBSET_E.md`, `PREREG_CONFIRM.md` and the CSVs in `results/`. Citation keys refer to `paper/references.md` (all verified). `[TBD-κ]` marks values that change after second-annotator adjudication; every score in this draft uses the single-annotator draft ground truth.
> Notation: R@|GT| = recall at the number of gold correspondences; *dev41* = development set, *confirm18* = held-out pre-registered set.

---

## 3 Data

### 3.1 Why operational schemas

A first pilot used CSV headers from 18 Indonesian *Satu Data* open-data portals. These turned out to be an easy matching problem. Only 6% of the headers contain abbreviations, and those are domain acronyms (`SD`, `RS`, `L/P`). A classic matcher (COMA [Do & Rahm 2002]) reached R@|GT| 0.93 on 10 natural cross-portal pairs, on par with an LLM (0.90). The abbreviation-heavy naming that makes Indonesian integration hard (`kd_kec`, `nm_pasien`, `stts_nikah`) lives in **operational system schemas**, not in published tables. We therefore build the benchmark from the DDL of open-source Indonesian information systems and pair them with the standards these systems must report to.

### 3.2 Sources

**Target standard.** HL7 FHIR R4 (4.0.1) [HL7 2019], the basis of Indonesia's national health exchange (SATUSEHAT) [Kemenkes 2023]. We use 11 resources that cover the clinical and administrative core of a hospital information system: Patient, Practitioner, Organization, Location, Encounter, Condition, Observation, MedicationRequest, Medication, DiagnosticReport, and ServiceRequest. Elements come from the official StructureDefinition snapshots: the top-level and backbone elements, without datatype expansion, and without `id`, `meta`, `text`, or extensions. That gives 13–46 elements per resource and **289 elements in total**.

**Development set (dev41).**
- 40 tables from SIMRS Khanza, the most widely used open-source hospital information system in Indonesia (1,189 tables in `sik.sql`).
- One citizen table from OpenSID (village administration).
- The 41 tables were chosen to cover all 11 resources: Observation 8, ServiceRequest 5, Patient/Organization/Location/MedicationRequest 4 each, Practitioner/Encounter/DiagnosticReport 3 each, Condition 2, Medication 1.

**Held-out confirmation set (confirm18).** 18 tables from six independent Indonesian clinic and community-health systems found on GitHub:
- a Laravel puskesmas medical-record system;
- a puskesmas queueing system;
- a CodeIgniter medical-record system;
- a posyandu growth-monitoring system;
- a student e-puskesmas project;
- the health module of the current OpenSID branch.

We excluded:
- systems derived from Khanza (they share its database);
- schemas with English identifiers;
- a dump that appeared to be the production EMR schema of a real hospital, exported from an internal server, because its provenance was unclear.

**Table 1. Benchmark statistics (FHIR pairs).**

| Set | System | Tables | Source columns | Columns/table | Abbreviated columns¹ | Gold 1:1 | n:1 | Ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev41 | SIMRS Khanza | 40 | 526 | 13.2 | 59% | 195 | 81 | 30 |
| | OpenSID | 1 | 60 | 60.0 | 45% | 10 | 1 | 0 |
| confirm18 | 6 systems | 18 | 127 | 7.1 | 33% | 69 | 6 | 10 |
| **Total** | 7 systems² | **59** | **713** | 12.1 | 53% | **274** | 88 | 40 |

¹ Columns with at least one vowel-poor token (vowel ratio < 0.34, length ≥ 3) or a two-letter acronym other than `id/at/by/of/to`. Examples: `kd_dokter`, `jk`, `no_rawat`, `pmrk_fisik`. ² OpenSID contributes to both sets (citizen table in dev41, health-module table in confirm18).

Beyond FHIR, the full sub-set also contains 13 pairs against other national standards: the SIAK civil-registry export format, the PDDikti Feeder higher-education API, and an OpenSID↔Khanza pairing. These are used only for the baseline in §5.1 [optional: move to appendix].

### 3.3 Annotation

Each source table is paired with the one FHIR resource it would be exported as. Annotators mark three kinds of label:
- **1:1 correspondences** (scored);
- **n:1 correspondences**: further source columns that map onto an element already used, e.g. `jam_reg` → `Encounter.period` when `tgl_registrasi` → `period` is the 1:1 link;
- **ambiguous** cases, each with a written reason.

Conventions:
1. **Base FHIR R4 only.** SATUSEHAT extensions (birth place, religion, mother's maiden name, citizenship) are not modelled, so such columns are true negatives.
2. **No datatype expansion.** Map to `name`, not `name.family`.
3. **Code vs. name of the same attribute** (`kd_kec`/`nm_kec`): the representative column is 1:1 and the other n:1, or the pair is ambiguous.
4. **A foreign key reachable only through a join** is ambiguous.
5. **Visit numbers in non-visit tables** (`no_rawat`) are references (`X.encounter`), not identifiers.
6. **Vital-sign tables:** the blood-pressure column → `component.value[x]` is 1:1, and the other vitals on the same row are n:1.
7. **Tariff and audit columns** are negatives unless they have a clear counterpart.

Under this scheme all gold correspondences of a table fall into a single resource. This property matters for §4.3 and §6.1.

The gold standard was drafted by one annotator. A second annotator, blind to the draft, annotated all 713 source columns of the 59 FHIR pairs [TBD-κ: Cohen's κ = …, raw agreement = …, 1:1-link F1 = …]. Disagreements were adjudicated [TBD]. Annotation guidelines and the annotation sheet are released with the benchmark.

### 3.4 Development/held-out protocol

All design decisions in §4 were made on dev41: the stage-1 catalogue, primary-resource selection, and selection rule. Before any matcher was run on confirm18, we wrote a pre-registration covering the frozen configurations, the hypotheses, the primary metric, the test and its correction, and the SHA-256 hashes of the confirm18 gold files. The run script refuses to execute if the hashes differ. The pre-registration is released with the code [cf. van Miltenburg et al. 2021].

### 3.5 Licensing and ethics

We release only table names, column names, and types, never data rows, together with our own annotations (CC BY 4.0).
- OpenSID and the FHIR specification are GPL-3.0 and CC0 respectively.
- Three of the confirmation systems are MIT-licensed by their authors.
- Khanza uses a custom free-use, non-commercial licence. Two repositories ship only the CodeIgniter framework licence. For these we requested permission from the authors [TBD: status]; until it is granted, they are available on request.
- No official schema of the national civil registry (SIAK) is public. Field lists circulating online come from a 2023 data-leak report, so we deliberately did not use them, and used the export template of OpenSID instead.

---

## 4 Method

### 4.1 Task

Given the column names (and types) of one source table, a matcher outputs scored correspondences to target elements. We study two target sizes:
- **Small target (oracle):** only the elements of the correct resource (13–46).
- **Large target:** the union of all 11 resources (289 elements, named `Resource.path`), with no indication of which resource is correct. This is the realistic integration setting, where an engineer has a table and a standard, not a pre-aligned pair.

Unless stated otherwise, the matcher does not see the source table name (§6.4 discusses this choice).

### 4.2 Matchers

- **Classic baselines:** COMA [Do & Rahm 2002], Cupid [Madhavan et al. 2001], and Similarity Flooding [Melnik et al. 2002] through Valentine [Koutras et al. 2021], on schema only. Instance-based matchers are not applicable because no data rows are released.
- **Embedding:** bge-m3 [Chen et al. 2024] cosine similarity over normalised names (snake/camel case split).
- **llm-full:** one prompt containing all source columns and all target elements. It asks for a JSON list of `{source, target, confidence}`.
- **hybrid (retrieve-and-rerank):** bge-m3 retrieves the top-k target elements per source column (k = 5, sensitivity k = 10), and one LLM prompt picks among each column's candidates [Sheetrit et al. 2024; Liu et al. 2025].
- **two-stage:**
  - **Stage 1:** the LLM sees the source columns and a catalogue of the 11 resources, and returns 1–3 resources, most likely first.
  - **Stage 2:** column matching as in llm-full, but against a reduced target, in one of two variants:
    - *union*: the elements of all picked resources in one prompt;
    - ***primary***: only the elements of the **rank-1** resource.

    The primary variant follows from the one-resource-per-table property of the task (§3.3).
- **oracle:** llm-full on the small target. It is the ceiling for stage 2.

**Abbreviation dictionary.** We mine an abbreviation→expansion dictionary from the Khanza DDL without gold data or external lexicons, using three heuristics:
- *context*: two identifiers that differ in one token (`nm_pasien` ~ `nama_pasien`);
- *acronym*: initial letters (`jk` ~ `jenis_kelamin`);
- *subsequence*: a vowel-poor token matched to a vocabulary word that contains it as a subsequence, ranked by shared neighbouring tokens.

This yields 201 entries. Precision is 75% (27/36) on tokens that occur in the evaluation tables and 25% (10/40) on a random held-out sample, where the long tail consists of medical acronyms. With the dictionary on, columns are shown as `nm_pasien (nama pasien)`, and embeddings use the expansion. The same Khanza dictionary is applied unchanged to confirm18, as a transfer test.

**Stage-1 catalogue.** Each resource is described by one of:
- the root `short` string of its StructureDefinition (one line, e.g. "A request for a service to be performed");
- the root `definition` (+ `comment`), our default after §5.4;
- `short` + top-level element names;
- the full "Scope and Usage" (+ "Boundaries and Relationships") text of the specification page.

### 4.3 Models and settings

- **Qwen3-8B** [Qwen Team 2025], run locally with Ollama on a laptop (Apple M3 Pro, 18 GB): temperature 0, seed 0, JSON mode, thinking disabled, 16k context, output capped at 3,000 tokens.
- **GLM-5.3-Flash** [Z.ai 2026] (open weights) through an OpenAI-compatible API: temperature 0, seed 0, JSON mode, minimum reasoning effort (reasoning cannot be disabled).

All prompts are byte-identical across models. Configurations were developed on Qwen only, and GLM was never used for tuning. Every LLM response is cached, so all reported numbers can be recomputed without model access.

### 4.4 Metrics and statistics

- **R@|GT|:** the fraction of gold 1:1 correspondences among a matcher's |GT| highest-scored predictions.
- **F1:** after greedy 1:1 assignment by score.
- **n:1-neutral:** n:1 and ambiguous pairs are removed from the predictions before scoring, so they are neither rewarded nor penalised (our first, strict metric penalised them; conclusions are unchanged, §5.4).

The unit of analysis is the table pair. We report mean differences with 95% bootstrap CIs (10k resamples) and Wilcoxon signed-rank tests. The confirmatory test is one-sided with Holm correction over two hypotheses. As a robustness check, we also report a correspondence-level analysis with cluster bootstrap and cluster sign-flip permutation over tables.

---

## 5 Results

### 5.1 Classic matchers fail on abbreviated schemas; LLMs do not (RQ1)

**Table 2. Schema-only baseline, R@|GT|, small target (28 pairs, strict metric).**

| Method | SIAKAD→Feeder (control) | OpenSID→SIAK | Khanza→SIAK | Khanza→OpenSID | Khanza→FHIR | OpenSID→FHIR |
| --- | --- | --- | --- | --- | --- | --- |
| COMA | 0.861 | 0.690 | 0.580 | 0.444 | 0.153 | 0.300 |
| Similarity Flooding | 0.861 | 0.391 | 0.535 | 0.278 | 0.090 | 0.400 |
| Cupid | 0.335 | 0.186 | 0.000 | 0.000 | 0.048 | 0.000 |
| bge-m3 | 0.861 | 0.491 | 0.374 | 0.389 | 0.178 | 0.500 |
| Qwen3-8B | 0.817 | 0.758 | 0.864 | 0.778 | **0.528** | 0.800 |

- On the control pair, where names are nearly identical across systems, every method reaches ≈0.86.
- With abbreviations on one side (Khanza→SIAK/OpenSID), classic matchers lose 30–40 points against the LLM.
- When abbreviation is combined with a language switch (Khanza→FHIR), COMA drops to 0.15 while the LLM keeps 0.53.

This hardest group, Khanza→FHIR, is the subject of the rest of the paper.

### 5.2 Small target: the abbreviation dictionary helps retrieval, not the LLM (RQ4)

On the 14 Khanza→FHIR pairs with the correct resource given:
- The **dictionary raises the hybrid matcher by +14.1 points** (k = 5, CI [+7, +22], p = 0.008) and the embedding retriever by +8.3. bge-m3 recall@10 rises from 0.58 to 0.69.
- The dictionary has **no effect on llm-full** (−0.9, p = 0.59): the 8B model already reads Khanza abbreviations.
- The hybrid stays well below llm-full (−28.4 points without the dictionary, p = 0.002). Its best variant (k = 10 + dictionary) only matches llm-full (−6.5, p = 0.18) while costing 3.5–4× the prompt tokens, because candidate lists are repeated per source column.

On small targets, the full prompt fits, and retrieval adds cost without adding accuracy.

### 5.3 Large target: accuracy halves, retrieval collapses

Replacing the single correct resource with the 289-element union roughly halves accuracy. On the first 15 dev pairs, llm-full+dict falls from 0.55 to 0.35, and hybrid+dict falls to 0.18.
- The hybrid is cheaper (−46 to −66% prompt tokens), but retrieval becomes the bottleneck: bge-m3 recall@10 is only 0.40, because names alone rarely identify the right resource.
- 54–59% of llm-full predictions fall into a resource other than the gold one.
- In a manually judged sample of 30 such cross-resource predictions, 6 were defensible, mostly foreign keys pointing at their referenced resource; 24 were plain errors.

### 5.4 Two-stage matching with a single primary resource (RQ2)

Table 3 is the main result.

**Table 3. Large target (289 elements), R@|GT| n:1-neutral (F1 in parentheses); mean prompt tokens per table.**

| Configuration | Qwen3-8B dev41 | Qwen3-8B confirm18 | GLM-5.3-Flash dev41 | GLM-5.3-Flash confirm18 | Prompt tokens |
| --- | --- | --- | --- | --- | --- |
| llm-full + dict | 0.270 (0.258) | 0.488 (0.435) | 0.556 (0.497) | 0.635 (0.569) | 1,870–1,940 |
| two-stage union | 0.338 (0.299) | 0.545 (0.453) | 0.581 (0.557) | 0.619 (0.579) | 980–1,340 |
| **two-stage primary** | **0.407 (0.389)** | **0.611 (0.520)** | **0.682 (0.653)** | **0.714 (0.669)** | **910–1,060** |
| *oracle (resource given)* | *0.552 (0.514)* | *0.791 (0.732)* | *0.764 (0.724)* | *0.824 (0.795)* | *250–310* |

**Table 4. Primary − llm-full, R@|GT| points [95% CI]; two-sided Wilcoxon p (confirmatory test on Qwen confirm18: one-sided, Holm).**

| Model | dev41 | confirm18 | pooled (59) |
| --- | --- | --- | --- |
| Qwen3-8B | +13.7 [+3.8, +23.7], p = 0.011 | +12.2 [−0.2, +27.2], p_Holm = 0.138 | +13.2 [+5.3, +21.5], p = 0.002 |
| GLM-5.3-Flash | +12.7 [+3.7, +21.7], p = 0.016 | +7.9 [−5.6, +22.2], p = 0.36 | +11.2 [+3.8, +18.7], p = 0.010 |

Four observations:
1. **Restricting stage 2 to one resource is the effective ingredient.** Union two-stage already halves the prompt, but its accuracy gain over llm-full is modest for Qwen (+6.8) and vanishes for the stronger GLM (+2.5 dev, −1.6 confirm). The primary variant adds +7 to +10 points on top of union for both models (GLM pooled: +9.9, p = 0.009).
2. **The effect replicates across model families without retuning.** For GLM, dev41 is an honest replication, because no design choice was made with GLM. Its effect (+12.7) is almost identical to Qwen's (+13.7).
3. **Pre-registered confirmation.**
   - On confirm18 the effect has the same size (+12.2 vs +13.7), but H1 is **not confirmed** at α = 0.05 (one-sided p = 0.069, p_Holm = 0.138).
   - Under our pre-registered criteria, the outcome is "direction consistent, not significant". The CI overlaps the dev41 CI.
   - Thirteen of 18 confirm18 pairs are ties: these schemas are less abbreviated (33% vs 59%), and all methods score alike on them.
   - H2 (primary > union) shows the same pattern: +6.5, p_Holm = 0.17.
4. **Cost.** The primary variant uses 48–55% of llm-full's prompt tokens: stage 1 ≈ 690 tokens plus one small matching prompt. On the local 8B model it is also faster (median 12–16 s vs 16–19 s per table).

**Robustness.** A correspondence-level analysis with tables as clusters gives the same ordering in all sets. It does not add power: the dev41 effect is +9.3 points (cluster-permutation p = 0.12), and the pooled effect is +10.2 (CI [+1.4, +19.3], p = 0.029). The micro effect is smaller because large tables, where all methods are similar, carry more weight. Rescoring with the strict metric changes no conclusion.

**Model strength.** GLM-5.3-Flash is 16–24 points more accurate than Qwen3-8B in every configuration (all p < 0.001), and its stage 1 ranks the right resource first in 83% of tables vs 63–67%. The gap between the primary variant and the oracle shrinks accordingly: from 14.6 to 8.2 points on dev41.

### 5.5 Design ablations on dev

All ablations below use Qwen3-8B on dev. None changed the frozen configuration except the `definition` catalogue.

| Ablation | Effect on R@|GT| | Note |
| --- | --- | --- |
| Source table name in stage 1 / stages 1+2 (n = 15) | −1.1 / −1.6, ns | fixes one stage-1 miss, breaks two others |
| ID→EN glossary (manual / LLM-generated) in llm-full (n = 15) | −9.8 / −11.3 (p = 0.03) | word-by-word glosses add noise on 289 elements |
| ID→EN glossary in two-stage (n = 15) | −1.3 / +3.3, ns | stage-1 picks unchanged |
| Stage-1 catalogue `definition` vs `short` (n = 41) | +1.5, ns | stage-1 hits on the 7 hardest tables: 0/7 → 3/7 |
| Catalogue with full "Scope and Usage" text (n = 41) | −0.1 / −2.1 (with Boundaries), ns | 13–23× longer stage-1 prompt, 2–3× slower |
| Per-resource stage 2, choose resource by summed LLM confidence / coverage (n = 41) | −10.2 / −12.9 vs rank-1 | the LLM is confident in any resource it is given |
| Negative stage-1 instruction ("do not rank first a resource the table only references") (n = 41) | −0.3 / −4.0, ns | rank-1 errors on Encounter double (§6.3) |
| Catalogue with element names (n = 41) | −0.2, ns | rank-1 hits 26 → 29, gains in tables that stay hard at stage 2 |

---

## 6 Failure analysis

### 6.1 Referenced resources absorb predictions

The largest single failure is not linguistic. Almost every clinical Khanza table carries the visit number `no_rawat`, so stage 1 includes Encounter for 24 of 41 tables. When Encounter is part of the union target, the model maps the table onto Encounter instead of the resource the table describes:

| Encounter in union? (31 non-Encounter tables whose correct resource was picked) | n | Share of top-|GT| predictions to Encounter | Share to correct resource | R@|GT| | Oracle | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| no | 17 | 0% | 76% | 0.60 | 0.73 | 0.13 |
| yes | 14 | 63% | 30% | 0.13 | 0.41 | **0.28** |

Tables that trigger Encounter are also intrinsically harder (oracle 0.41 vs 0.73). Even so, the gap to the oracle doubles.

A typical case is the referral table `rujuk`, with ServiceRequest correctly in the union:
- `no_rujuk` → `Encounter.identifier`
- `kd_dokter` → `Encounter.participant.individual`
- `tgl_rujuk` → `Encounter.hospitalization.origin`

This scores R@|GT| 0 against an oracle of 0.62.

This is why the primary variant works. Under the annotation convention, every correspondence of a table lies in one resource, and a foreign key such as `no_rawat` maps to `X.encounter`, not to an Encounter element. The same absorption appears in confirm18 in other forms: `tb_rujuk` → Encounter first, and a visit×drug link table → Medication instead of MedicationRequest. It persists with the stronger GLM model, whose union variant gains nothing over llm-full.

### 6.2 FHIR modelling knowledge, not Indonesian vocabulary

Referral and order tables (`rujuk`, `rujuk_masuk`, `rujukan_internal_poli`, `permintaan_lab`, `permintaan_radiologi`) were never assigned to ServiceRequest by Qwen's stage 1 (0/5). We first suspected a vocabulary gap, because *rujuk* = "refer" is an Indonesian domain term, not an abbreviation. But a glossary that labelled the column `rujuk_ke (EN: refer to)` left every stage-1 decision unchanged. The model knows what *rujuk* means. What it lacks is the modelling convention that a referral is a FHIR ServiceRequest.

Giving stage 1 the official `definition` text, which mentions referrals, recovered 3 of the 7 hardest tables. Longer specification text did not help further. The "Scope and Usage" section of ServiceRequest explains that a request "will lead to" a DiagnosticReport or Observation, and the 8B model then picks those resources instead. Lab and radiology *orders* went to DiagnosticReport (the report) in every catalogue variant.

### 6.3 Negative instructions prime the model

An instruction that named the failure explicitly backfired: "Do not put first a resource the table only points to through a foreign key: a column holding the identifier of a visit, a patient or a practitioner is a reference to an Encounter, Patient or Practitioner…". Encounter as a wrong rank-1 choice rose from 7 to 14 of 41 tables, mostly vital-sign tables that had previously been correct, and rank-1 accuracy fell from 26/41 to 23/41. Naming the resource to avoid made the 8B model more likely to choose it.

### 6.4 Generic columns need the table name

In one confirmation system, Qwen scores R@|GT| = 0 in every non-oracle configuration and GLM only 0.11–0.28, while their oracles score 0.89 and 0.78. The tables `polis` (`id, nama, nomor_sekarang`), `tenaga_kesehatans` (`id, poli_id, nama, jadwal, no_telepon`), and `antrians` cannot be told apart from their columns alone. Qwen's stage 1 defaults to Patient, and GLM's to Encounter for the clinic-department table. On Khanza, adding the table name gave no gain (§5.5), because Khanza columns already carry domain prefixes (`kd_poli`, `nm_dokter`). For schemas with generic names, the table name is likely decisive. We leave this conditional effect to future work, because confirm18 is now spent.

### 6.5 What remains: choosing the primary resource

With the right resource among the stage-1 picks, choosing it perfectly (selection ceiling) would give 0.508 on dev41 (Qwen), only 4.4 points below the oracle (0.552, ns). The remaining gap is therefore almost entirely a **resource-selection** problem. Three cheap signals failed: LLM confidence (§5.5), richer descriptions (§6.2), and instructions (§6.3).

The stronger model narrows the gap substantially (rank-1 accuracy 83% vs 63%). This suggests that resource selection, more than column matching, is where model capacity pays off for standards-based integration. A practical deployment can also use the source table name (§6.4) or a human confirmation of the resource, which is a one-click decision, compared with hundreds of column decisions.
