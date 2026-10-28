# Draft — Sections 1, 2, 7, 8

> Working draft, 28 Oct 2026. Citation keys refer to `paper/references.md`; every entry there was checked against OpenAlex/DOI or the official source. `[TBD-κ]` = filled after second-annotator adjudication.

---

## 1 Introduction

Indonesia is moving its health data onto a national exchange. Minister of Health Regulation No. 24/2022 obliges every health facility, from independent practices and *puskesmas* (community health centres) to hospitals, to keep electronic medical records by the end of 2023 [Kemenkes 2022]. The SATUSEHAT platform integrates those records using HL7 FHIR R4 [HL7 2019; Kemenkes 2023]. In parallel, the *Satu Data Indonesia* policy requires government data producers to follow shared standards, metadata, and interoperability rules [Perpres 39/2019].

For the thousands of facilities that run locally developed or open-source information systems, compliance comes down to a **schema-matching** problem: deciding which column of which local table corresponds to which element of which FHIR resource. A data engineer can solve it, but slowly, one table and one column at a time.

Schema matching has a long history [Rahm & Bernstein 2001], with mature lexical and structural matchers [Madhavan et al. 2001; Do & Rahm 2002; Melnik et al. 2002] and benchmarks to compare them [Koutras et al. 2021]. Recent work shows that large language models (LLMs) can match schemas from names and descriptions alone [Parciak et al. 2024]. They can be combined with retrieval to scale to large targets [Sheetrit et al. 2024; Liu et al. 2025], and they are already being applied to biomedical standards [Seedat & van der Schaar 2024; Santos et al. 2024; Li et al. 2024].

Two features of the Indonesian setting are not covered by this literature:
1. **Language and naming style.** Source schemas are written in Indonesian, often in a terse abbreviated style (`kd_dokter`, `stts_nikah`, `tgl_registrasi`), while the target standard is in English. Column-name abbreviation is a recognised problem in English [Zhang et al. 2023; Cai et al. 2025], but no benchmark pairs abbreviated non-English operational schemas with an international standard.
2. **Unknown target resource.** A hospital table must be mapped into a standard of hundreds of elements without knowing in advance which resource it belongs to. Most benchmarks evaluate a source table against a pre-selected target table.

We ask four questions:
- **RQ1:** How do classic matchers and LLMs compare on abbreviated Indonesian schemas?
- **RQ2:** How should an LLM-based matcher be organised when the target is a whole standard rather than one table?
- **RQ4:** Does an automatically mined abbreviation dictionary help?
- **RQ5:** Can an open model on a laptop do this, and how much does a stronger open model add?

(We number the questions as in our study protocol; the cross-lingual question RQ3 is deferred, §7.)

**Contributions.**
1. **A benchmark of Indonesian operational schemas mapped to FHIR R4** (§3). It has 59 tables from 7 open-source systems, 713 source columns, and 274 gold correspondences into a 289-element target (11 FHIR resources). It comes with annotation conventions, a development/held-out split, and a pre-registered confirmation protocol. A pilot on open-government data shows why operational schemas are needed: published open-data headers are rarely abbreviated, and classic matchers already solve them.
2. **A simple, effective matching recipe for whole-standard targets** (§4–5). Ask the LLM for the resource first, using the standard's own resource definitions, then match columns **only against the top-ranked resource**. Compared with a single prompt over the full target, this gains +12.7 to +13.7 points R@|GT| on the development set at about half the prompt tokens. The gain replicates across two model families without retuning (Qwen3-8B, GLM-5.3-Flash). On a pre-registered held-out set, the effect has the same size (+12.2) but is not statistically confirmed (p_Holm = 0.14, n = 18). Restricting matching to one resource matters more than shrinking the target: matching against the union of candidate resources gains little and nothing at all for the stronger model.
3. **A failure analysis** (§6). The dominant errors are about FHIR modelling, not language:
   - resources referenced through a foreign key (the visit number) absorb the predictions of the table that references them;
   - referrals and orders are not recognised as ServiceRequest even when the model understands the Indonesian term;
   - longer specification text and explicitly worded negative instructions make stage-1 resource selection worse, the latter by priming the very resource they forbid.

   A mined abbreviation dictionary helps embedding retrieval and retrieve-and-rerank (+8 and +14 points) but not full-prompt LLM matching.

We release the gold annotations, guidelines, code, all cached model outputs, and the pre-registration [TBD: URL].

---

## 2 Related work

**Schema matching.** Classic matchers combine lexical similarity of element names, structure, and constraints. Examples are Cupid [Madhavan et al. 2001], COMA [Do & Rahm 2002], and Similarity Flooding [Melnik et al. 2002]; see the survey of Rahm & Bernstein [2001]. Valentine [Koutras et al. 2021] re-implements these and instance-based matchers under one evaluation framework, and we use it for our baselines. Learned matchers, from attention models trained on clinical schema pairs [Zhang et al. 2021] to multi-task matching models [Tu et al. 2023], need labelled pairs that rarely exist for a new national standard.

**LLMs for schema matching.**
- Parciak et al. [2024] study off-the-shelf LLMs that match relational schemas from names and descriptions on a health-domain benchmark. They find that quality suffers both from too little and from too much context, which our stage-1 results echo (§6.2).
- ReMatch [Sheetrit et al. 2024] adds retrieval so that LLMs can match large schemas without training data.
- Magneto [Liu et al. 2025] combines a fine-tuned small retriever with LLM reranking and introduces a biomedical benchmark.
- Matchmaker [Seedat & van der Schaar 2024] composes candidate generation, refinement, and confidence scoring into a self-improving LLM program, evaluated on medical schema matching.
- LLMatch [Wang et al. 2026] proposes a unified LLM-based schema-matching framework.
- General data-preprocessing LLMs such as Jellyfish [Zhang et al. 2024] include matching among their tasks.

Our retrieve-and-rerank baseline follows the Magneto/ReMatch design. Our two-stage matcher differs in what the first stage selects: a *target resource* from the standard's own catalogue rather than candidate elements per column. It also differs in insisting on a single resource in the second stage. We show that this restriction, not the reduction in target size, carries the gain.

**Biomedical and FHIR mapping.** GDC-SM [Santos et al. 2024] maps cancer-study datasets onto the Genomic Data Commons standard with expert alignments. FHIR-GPT [Li et al. 2024] uses LLMs to transform EHR content into FHIR resources, with a focus on unstructured clinical text. Our task is the structured counterpart: aligning the *schema* of a hospital database with FHIR. It adds two difficulties the above do not have: the source is non-English and abbreviated, and the right resource is unknown.

**Abbreviated column names.** NameGuess [Zhang et al. 2023] formulates column-name expansion as a generation task. Columbo [Cai et al. 2025] shows that real enterprise abbreviations are harder than synthetic ones and expands them with an LLM pipeline. Both target English. Our dictionary is mined from the source DDL itself without labels or an LLM, and we evaluate its effect on matching rather than on expansion accuracy. Comparing against an LLM expander such as Columbo is left to future work (§7).

**Indonesian NLP resources.** Benchmarks for Indonesian and its local languages cover natural-language understanding, generation, and sentiment [Wilie et al. 2020; Cahyawijaya et al. 2021; Winata et al. 2023]. We are not aware of an Indonesian benchmark for data integration or schema matching.

**Evaluation methodology.** We follow the case for pre-registration in NLP [van Miltenburg et al. 2021] for our confirmation set. Because our sources are public GitHub schemas, we discuss data contamination [Sainz et al. 2023] in §7. Our observation that a negated instruction raises the error it forbids (§6.3) is consistent with known weaknesses of LMs on negated prompts [Jang et al. 2022]. The harm from long specification text (§6.2) is consistent with known long-context degradation [Liu et al. 2024].

---

## 7 Limitations

- **Annotation.** The gold standard was drafted by one annotator, and a second annotator independently labelled all 59 FHIR tables [TBD-κ]. Reported scores use [TBD: the adjudicated / the draft] gold standard. Our conventions are themselves design choices that a different team could make differently: base FHIR without SATUSEHAT profiles, no datatype expansion, foreign keys to `X.encounter`.
- **The single-resource convention favours the primary method.** Our conventions place all gold correspondences of a table in one resource, and the primary variant exploits exactly that. We consider the convention realistic for export to FHIR, where one table row is serialised as one resource instance plus references. But tables that genuinely populate several resources (e.g. a registration table that creates both a Patient and an Encounter) would be under-served by the primary variant, and our benchmark does not measure this.
- **Statistical power.** The pair is the unit of analysis, and per-pair differences have a standard deviation around 0.28, so effects of 10 points need 120–200 pairs for 80% power. With n = 18, the pre-registered test was underpowered and did not reach significance; we report it as such. Pooled and correspondence-level analyses support the effect but include development data.
- **Single runs and nondeterminism.** Each configuration was run once at temperature 0. The local model is deterministic given the cache. API decoding at temperature 0 is not guaranteed to be.
- **Scope of the target.** We cover 11 of the roughly 145 FHIR R4 resources and use column names and types only: no column comments, no data values, no table names. The last choice is deliberate (§4.1), but §6.4 shows that it penalises schemas with generic column names.
- **Representativeness.** Development data are dominated by one system (Khanza, 40 of 41 tables), and the held-out systems are smaller and less abbreviated (33% vs 59% of columns). The held-out set has now been used and cannot serve as a clean test for further development.
- **Contamination.** All source schemas and the FHIR specification are public, so they may appear in the models' training data. Our gold correspondences and conventions do not.
- **Models.** Two open-weight models from two families. We did not evaluate proprietary frontier models, and our efficiency claims are in prompt tokens, which do not translate one-to-one into price or latency.
- **Deferred questions.** We do not report the controlled cross-lingual comparison (RQ3: the same pairs in three language variants), and we do not compare our mined dictionary with an LLM-based expander such as Columbo. Both are future work.

---

## 8 Conclusion

Mapping the database of an Indonesian hospital or *puskesmas* onto FHIR is hard for classic matchers and still far from solved for LLMs. When the whole standard is the target, accuracy roughly halves, and most errors put the right attribute into the wrong resource. A two-step procedure fixes a large share of this at half the prompt cost: choose the resource first, from the standard's own definitions, and then match only against that one resource. The improvement is consistent across two model families and in the same direction on a pre-registered held-out set, though not statistically confirmed there.

The errors that remain are about knowing how FHIR models a hospital's world: a referral is a ServiceRequest, and a visit number is a reference, not an identity. They are not about reading Indonesian or decoding abbreviations. Choosing the primary resource is now the main bottleneck, and a single human confirmation of that choice is a cheap safeguard in practice.

We release the benchmark, conventions, code, cached outputs, and pre-registration to support work on matching against national standards in languages other than English.
