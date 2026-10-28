%title Single-Resource Two-Stage LLM Matching of Indonesian Hospital Schemas to FHIR
%authors [First Author]*^1^, [Second Author]^2^
%affil ^1,2^[Department, Faculty, University; address; country]
%email e-mail: *^1^[email], ^2^[email]

%abstrak
Fasilitas kesehatan di Indonesia wajib mengirim rekam medis elektronik ke platform SATUSEHAT dalam format HL7 FHIR R4, sehingga integrasi data menjadi masalah pencocokan skema antara skema basis data berbahasa Indonesia yang bersingkatan dan standar berbahasa Inggris. Penelitian ini membangun benchmark berisi 59 tabel dari tujuh sistem informasi kesehatan open-source Indonesia dengan 274 korespondensi beranotasi ke 289 elemen FHIR, dibagi menjadi set pengembangan dan set uji yang dipra-registrasi. Pencocok klasik gagal pada skema ini (COMA R@|GT| 0,15 dibanding 0,53 untuk LLM 8B). Ketika seluruh standar menjadi target, satu prompt LLM kehilangan sekitar separuh akurasinya. Kami mengusulkan pencocok dua tahap yang memilih resource FHIR dari definisi resminya, lalu mencocokkan kolom hanya ke resource peringkat pertama. Metode ini menaikkan recall 12,7–13,7 poin dibanding prompt penuh dengan sekitar separuh token prompt, baik untuk Qwen3-8B maupun GLM-5.3-Flash tanpa penyetelan ulang. Pada set uji, besar efeknya sama tetapi belum signifikan secara statistik (n = 18). Analisis galat menunjukkan bahwa kesalahan yang tersisa berkaitan dengan pemodelan FHIR, misalnya resource yang dirujuk lewat foreign key menyerap prediksi, bukan dengan kosakata atau singkatan bahasa Indonesia.
%katakunci pencocokan skema, large language model, HL7 FHIR, sistem informasi kesehatan, interoperabilitas

%abstract
Indonesian health facilities must report electronic medical records to the national SATUSEHAT platform in HL7 FHIR R4, which turns data integration into a schema-matching problem between abbreviated Indonesian database schemas and an English standard. We build a benchmark of 59 tables from seven open-source Indonesian health information systems, with 274 annotated correspondences into 289 FHIR elements, split into a development set and a pre-registered held-out set. Classic matchers fail on these schemas (COMA R@|GT| 0.15 vs. 0.53 for an 8B LLM). When the whole standard is the target, a single LLM prompt loses about half of its accuracy. We propose a two-stage matcher that selects the FHIR resource from its official definition and then matches columns only against the top-ranked resource. It improves recall by 12.7–13.7 points over the full prompt at about half the prompt tokens, for both Qwen3-8B and GLM-5.3-Flash without retuning. On the held-out set the effect has the same size but is not statistically confirmed (n = 18). Error analysis shows that the remaining errors concern FHIR modelling, such as resources referenced through foreign keys absorbing predictions, rather than Indonesian vocabulary or abbreviations.
%keywords schema matching, large language models, HL7 FHIR, health information systems, interoperability

# 1. INTRODUCTION

Indonesia is moving its health data onto a national exchange. Minister of Health Regulation No. 24/2022 obliges every health facility, from independent practices and community health centres (*puskesmas*) to hospitals, to keep electronic medical records by the end of 2023 [@kemenkes2022]. The SATUSEHAT platform integrates these records using HL7 FHIR R4 [@kemenkes2023; @hl7fhir]. In parallel, the *Satu Data Indonesia* policy requires government data producers to follow shared data standards, metadata and interoperability rules [@perpres39]. For the thousands of facilities that run locally developed or open-source information systems, compliance is a schema-matching problem. An engineer has to decide which column of which local table corresponds to which element of which FHIR resource, table by table and column by column.

Schema matching has mature lexical and structural solutions such as Cupid [@cupid], COMA [@coma] and Similarity Flooding [@simflood], and frameworks such as Valentine compare them on common benchmarks [@valentine]. Learned matchers, from attention models trained on clinical schema pairs [@smat] to multi-task matching models [@unicorn], need labelled pairs that rarely exist for a new national standard. Large language models (LLMs) can match schemas from names and descriptions alone, although quality suffers both from too little and from too much context [@parciak]. Retrieval lets LLM matchers scale to large schemas without training data [@rematch], and retrieve-and-rerank pipelines combine small and large models [@magneto]. Matchmaker composes candidate generation, refinement and confidence scoring into a self-improving program for medical schemas [@matchmaker]. Other recent work proposes unified LLM matching frameworks [@llmatch] or general data-preprocessing LLMs [@jellyfish]. In the biomedical domain, GDC-SM maps cancer-study data onto the Genomic Data Commons standard [@gdcsm], and FHIR-GPT transforms clinical text into FHIR resources [@fhirgpt]. Column-name abbreviation is a recognised problem in English tables, addressed by NameGuess [@nameguess] and Columbo [@columbo]. Indonesian NLP now has benchmarks for understanding, generation and sentiment [@indonlg; @nusax], but not for data integration.

Two features of the Indonesian setting are not covered by this literature. First, the source schemas are Indonesian and often abbreviated (`kd_dokter`, `stts_nikah`, `tgl_registrasi`), while the standard is English. Second, a hospital table must be mapped into a standard of hundreds of elements without knowing in advance which resource it belongs to; most benchmarks match a source table against a pre-selected target table. This paper addresses both. Its contributions are: (i) a benchmark of 59 tables from seven open-source Indonesian systems mapped to FHIR R4, with annotation conventions, a development/held-out split and a pre-registered confirmation protocol; (ii) a two-stage matcher that first selects the target resource and then matches columns against that single resource only, evaluated with two open model families; and (iii) an error analysis showing that the remaining failures concern FHIR modelling knowledge rather than language.

# 2. METHODS

## 2.1 Benchmark construction

A pilot with column headers from 18 Indonesian open-data portals showed that published open-data tables are an easy matching problem: only 6% of headers contained abbreviations, and COMA reached R@|GT| 0.93 on cross-portal pairs, on par with an LLM (0.90). Abbreviated naming lives in operational system schemas, so the benchmark is built from the DDL of open-source Indonesian information systems.

The target standard is HL7 FHIR R4 (4.0.1) [@hl7fhir]. We use 11 resources that cover the clinical and administrative core of a hospital system: Patient, Practitioner, Organization, Location, Encounter, Condition, Observation, MedicationRequest, Medication, DiagnosticReport and ServiceRequest. Elements are taken from the official StructureDefinition snapshots at the top and backbone level, without datatype expansion and without technical elements (`id`, `meta`, `text`, extensions). This gives 13–46 elements per resource and 289 elements in total. The development set (*dev41*) has 40 tables of SIMRS Khanza, the most widely used open-source hospital information system in Indonesia, plus one citizen table of OpenSID; the 41 tables cover all 11 resources. The held-out confirmation set (*confirm18*) has 18 tables from six independent clinic and community-health systems found on GitHub. We excluded systems derived from Khanza, schemas with English identifiers, and a dump that appeared to be the production schema of a real hospital, because its provenance was unclear. Table 1 summarises the benchmark.

Table 1 Benchmark statistics per source system (FHIR pairs); abbreviated = column with a vowel-poor token or a two-letter acronym
| Set | System (licence) | Tables | Columns | Abbreviated | Gold 1:1 | n:1 | Ambiguous |
| dev41 | SIMRS Khanza, hospital (custom, non-commercial) | 40 | 526 | 59% | 195 | 81 | 30 |
| dev41 | OpenSID, village administration (GPL-3.0) | 1 | 60 | 45% | 10 | 1 | 0 |
| confirm18 | puskesmas medical records, Laravel (MIT) | 5 | 51 | 53% | 22 | 3 | 5 |
| confirm18 | puskesmas queueing, Laravel (MIT) | 3 | 18 | 11% | 8 | 0 | 2 |
| confirm18 | clinic medical records, CodeIgniter (unclear) | 6 | 29 | 24% | 23 | 2 | 1 |
| confirm18 | posyandu growth monitoring (MIT) | 2 | 16 | 25% | 11 | 1 | 2 |
| confirm18 | student e-puskesmas project (unclear) | 1 | 5 | 20% | 2 | 0 | 0 |
| confirm18 | OpenSID health module (GPL-3.0) | 1 | 8 | 13% | 3 | 0 | 0 |
| Total | 7 systems | 59 | 713 | 53% | 274 | 88 | 40 |

Each source table is paired with the one FHIR resource it would be exported as. The annotator marks 1:1 correspondences (scored), n:1 correspondences (further columns mapping onto an element already used, e.g. `jam_reg` → `Encounter.period` when `tgl_registrasi` → `period` is the 1:1 link), and ambiguous cases with a reason. The conventions are: base FHIR R4 only, so SATUSEHAT extensions such as birth place and religion are true negatives; no datatype expansion; a foreign key reachable only through a join is ambiguous; a visit number in a non-visit table is a reference (`X.encounter`), not an identifier; in vital-sign tables the blood-pressure column maps to `component.value[x]` and the other vitals are n:1; and tariff and audit columns are negatives. Under these conventions all gold correspondences of a table lie in one resource. Table 2 shows the annotation of one development table.

Table 2 Annotation example: Khanza `reg_periksa` (outpatient registration) → FHIR Encounter
| Source column | Meaning | FHIR element | Label |
| no_rawat | visit number | identifier | 1:1 |
| tgl_registrasi | registration date | period | 1:1 |
| jam_reg | registration time | period | n:1 |
| kd_dokter | doctor code | participant.individual | 1:1 |
| no_rkm_medis | medical record number | subject | 1:1 |
| kd_poli | clinic code | location.location | 1:1 |
| stts | visit status | status | 1:1 |
| status_lanjut | outpatient / inpatient | class | 1:1 |
| kd_pj | payer code | account | ambiguous |
| hubunganpj | relation of responsible person | participant.type | ambiguous |

The gold standard was drafted by one annotator, and a second annotator independently labelled all 713 columns [TBD: Cohen's κ, adjudication].

All design decisions in Section 2.2 were made on dev41. Before any matcher was run on confirm18, a pre-registration fixed the configurations, hypotheses, primary metric, test and correction, and the SHA-256 hashes of the confirm18 gold files; the run script refuses to execute if the hashes differ [@prereg]. Only table names, column names and types are released, together with our annotations; licences of the sources are documented in the release.

## 2.2 Matchers

All matchers see column names and types only, without data rows and without the source table name. Two target sizes are studied: the small target (*oracle*), which contains only the correct resource, and the large target, which is the union of all 11 resources (289 elements named `Resource.path`) with no indication of the correct one.

The classic baselines are COMA, Cupid and Similarity Flooding through Valentine [@valentine], and the embedding baseline is cosine similarity of bge-m3 [@bgem3] over normalised names. The *llm-full* matcher sends one prompt with all source columns and all target elements and asks for a JSON list of correspondences with confidences. The *hybrid* matcher retrieves the top-k elements per source column with bge-m3 (k = 5, sensitivity k = 10), and one LLM prompt chooses among each column's candidates, following retrieve-and-rerank designs [@rematch; @magneto].

The proposed *two-stage* matcher works as follows. In stage 1, the LLM sees the source columns and a catalogue of the 11 resources and returns one to three resources, most likely first. Each resource is described by the root `definition` text of its StructureDefinition; alternatives evaluated on dev41 were the one-line `short` text, `short` plus element names, and the full "Scope and Usage" section of the specification. In stage 2, columns are matched as in llm-full against a reduced target, either the union of all selected resources (*union*) or only the rank-1 resource (*primary*). The primary variant follows from the one-resource-per-table property of the task. Figure 1 shows the pipeline together with the two reference configurations.

![fig](fig1_pipeline.png)
Figure 1 Two-stage matcher with a single primary resource, illustrated with Khanza `resep_obat` (prescriptions); the ranking is the actual Qwen3-8B stage-1 output and the stage-2 mappings shown are gold correspondences

An abbreviation dictionary is mined from the Khanza DDL without gold data or external lexicons. It uses identifiers that differ in one token (`nm_pasien` ~ `nama_pasien`), initial letters (`jk` ~ `jenis_kelamin`), and vowel-poor tokens matched to vocabulary words that contain them as a subsequence, ranked by shared neighbouring tokens. The 201 entries have a precision of 75% on tokens in the evaluation tables and 25% on a random held-out sample, where medical acronyms dominate. With the dictionary on, a column is shown as `nm_pasien (nama pasien)`. The same Khanza dictionary is applied unchanged to confirm18.

## 2.3 Models, metrics and statistics

Qwen3-8B [@qwen3] runs locally with Ollama on a laptop (Apple M3 Pro, 18 GB) at temperature 0, seed 0, JSON mode and thinking disabled. GLM-5.3-Flash [@glm] is an open-weight model accessed through an OpenAI-compatible API at temperature 0, seed 0, JSON mode and the minimum reasoning effort. Prompts are byte-identical across models; configurations were developed on Qwen only, and every response is cached so that all numbers can be recomputed.

The primary metric is R@|GT|, the fraction of gold 1:1 correspondences among a matcher's |GT| highest-scored predictions. F1 is computed after greedy one-to-one assignment by score. Both are n:1-neutral: n:1 and ambiguous pairs are removed from the predictions before scoring. The table pair is the unit of analysis. We report mean differences with 95% bootstrap confidence intervals (10,000 resamples) and Wilcoxon signed-rank tests; the confirmatory test is one-sided with Holm correction over two hypotheses. A correspondence-level analysis with cluster bootstrap and cluster sign-flip permutation over tables is used as a robustness check.

# 3. RESULTS AND DISCUSSION

## 3.1 Classic matchers and LLMs on abbreviated schemas

Table 3 compares schema-only matchers on the small target. On the control pair, where names are nearly identical across two academic systems, every method reaches about 0.86. With abbreviations on one side (Khanza to the civil-registry export format SIAK or to OpenSID), classic matchers lose 30–40 points against the LLM. When abbreviation is combined with a language switch (Khanza to FHIR), COMA drops to 0.15 while the LLM keeps 0.53. This hardest group is the subject of the remaining experiments.

Table 3 Schema-only baseline, R@|GT| on the small target (28 pairs)
| Method | Control | OpenSID→SIAK | Khanza→SIAK | Khanza→OpenSID | Khanza→FHIR |
| COMA | 0.861 | 0.690 | 0.580 | 0.444 | 0.153 |
| Similarity Flooding | 0.861 | 0.391 | 0.535 | 0.278 | 0.090 |
| Cupid | 0.335 | 0.186 | 0.000 | 0.000 | 0.048 |
| bge-m3 | 0.861 | 0.491 | 0.374 | 0.389 | 0.178 |
| Qwen3-8B | 0.817 | 0.758 | 0.864 | 0.778 | 0.528 |

On the 14 Khanza→FHIR pairs with the correct resource given, the abbreviation dictionary raises the hybrid matcher by 14.1 points (k = 5, CI [7, 22], p = 0.008) and the embedding retriever by 8.3 points, and bge-m3 recall@10 rises from 0.58 to 0.69. It has no effect on llm-full (−0.9, p = 0.59), which already reads Khanza abbreviations. The hybrid stays below llm-full (−28.4 points without the dictionary, p = 0.002); its best variant (k = 10 with dictionary) only matches llm-full while using 3.5–4 times as many prompt tokens. On a small target, the full prompt fits and retrieval adds cost without adding accuracy.

## 3.2 The large target and the two-stage matcher

Replacing the correct resource with the 289-element union roughly halves accuracy: on the first 15 development pairs, llm-full with dictionary falls from 0.55 to 0.35 and the hybrid to 0.18. Retrieval becomes the bottleneck, as bge-m3 recall@10 drops to 0.40, and 54–59% of llm-full predictions fall into a resource other than the gold one. Table 4 shows the main result on the large target.

Table 4 Large target (289 elements), R@|GT| with F1 in parentheses, and mean prompt tokens per table
| Configuration | Qwen3-8B dev41 | Qwen3-8B confirm18 | GLM dev41 | GLM confirm18 | Prompt tokens |
| llm-full | 0.270 (0.258) | 0.488 (0.435) | 0.556 (0.497) | 0.635 (0.569) | 1,870–1,940 |
| two-stage union | 0.338 (0.299) | 0.545 (0.453) | 0.581 (0.557) | 0.619 (0.579) | 980–1,340 |
| two-stage primary | 0.407 (0.389) | 0.611 (0.520) | 0.682 (0.653) | 0.714 (0.669) | 910–1,060 |
| oracle (resource given) | 0.552 (0.514) | 0.791 (0.732) | 0.764 (0.724) | 0.824 (0.795) | 250–310 |

Table 5 Primary minus llm-full in R@|GT| points [95% CI], with Wilcoxon p (Qwen confirm18: pre-registered one-sided test, Holm-corrected)
| Model | dev41 | confirm18 | pooled (59 tables) |
| Qwen3-8B | +13.7 [3.8, 23.7], p = 0.011 | +12.2 [−0.2, 27.2], p = 0.138 | +13.2 [5.3, 21.5], p = 0.002 |
| GLM-5.3-Flash | +12.7 [3.7, 21.7], p = 0.016 | +7.9 [−5.6, 22.2], p = 0.36 | +11.2 [3.8, 18.7], p = 0.010 |

Restricting stage 2 to one resource is the effective ingredient. The union variant already halves the prompt, but its gain over llm-full is modest for Qwen (+6.8 points on dev41) and vanishes for the stronger GLM (+2.5 on dev41, −1.6 on confirm18). The primary variant adds 7–10 points on top of union for both models (GLM pooled: +9.9, p = 0.009). The gain is not uniform across resources (Table 6). It is largest where the referenced-resource problem of Section 3.3 is strongest, such as MedicationRequest, Organization and, for GLM, ServiceRequest. It is negative where the rank-1 choice is often wrong, such as Practitioner for Qwen, whose stage 1 ranks Patient first for staff tables, and Location for GLM.

Table 6 R@|GT| per FHIR resource on all 59 tables (n = tables)
| Resource | n | Qwen llm-full | Qwen primary | Qwen oracle | GLM llm-full | GLM primary | GLM oracle |
| Patient | 7 | 0.75 | 0.74 | 0.76 | 0.82 | 0.76 | 0.84 |
| Practitioner | 6 | 0.44 | 0.30 | 0.82 | 0.75 | 0.83 | 0.98 |
| Organization | 5 | 0.20 | 0.93 | 0.93 | 0.73 | 0.73 | 0.93 |
| Location | 6 | 0.65 | 0.75 | 0.88 | 0.78 | 0.58 | 0.92 |
| Encounter | 6 | 0.34 | 0.37 | 0.59 | 0.45 | 0.74 | 0.74 |
| Condition | 2 | 0.25 | 0.67 | 0.42 | 0.42 | 0.50 | 0.67 |
| Observation | 9 | 0.07 | 0.19 | 0.34 | 0.33 | 0.57 | 0.73 |
| MedicationRequest | 6 | 0.12 | 0.47 | 0.62 | 0.58 | 0.75 | 0.64 |
| Medication | 3 | 0.87 | 0.80 | 0.47 | 1.00 | 1.00 | 0.60 |
| DiagnosticReport | 3 | 0.06 | 0.36 | 0.30 | 0.07 | 0.42 | 0.69 |
| ServiceRequest | 6 | 0.06 | 0.00 | 0.55 | 0.41 | 0.67 | 0.69 |

The effect also replicates across model families: no design choice was made with GLM, so its dev41 result is an independent replication, and its size (+12.7) is almost identical to Qwen's (+13.7). The primary variant uses 48–55% of the prompt tokens of llm-full, about 690 for stage 1 plus one small matching prompt, and on the local model it is also faster (median 12–16 s against 16–19 s per table). GLM is 16–24 points more accurate than Qwen in every configuration (all p < 0.001), and its stage 1 ranks the correct resource first for 83% of tables against 63–67%, which shrinks the gap between primary and oracle from 14.6 to 8.2 points on dev41.

On confirm18 the effect has the same size as on dev41 (+12.2 against +13.7), but the pre-registered hypothesis that primary outperforms llm-full is not confirmed at α = 0.05 (one-sided p = 0.069, Holm-corrected p = 0.138). By the pre-registered criteria the outcome is "direction consistent, not significant": the confidence interval overlaps that of dev41. Thirteen of the 18 held-out tables are ties, because these schemas are smaller and less abbreviated (33% against 58% of columns) and all methods score alike on them. The second hypothesis (primary outperforms union) shows the same pattern (+6.5, Holm-corrected p = 0.17). A correspondence-level analysis with tables as clusters gives the same ordering in all sets but no additional power: the dev41 effect is +9.3 points (cluster-permutation p = 0.12) and the pooled effect +10.2 (CI [1.4, 19.3], p = 0.029), smaller because large tables, on which all methods are similar, carry more weight.

Design ablations on dev41 with Qwen did not change the configuration except for the catalogue. Replacing the one-line `short` text with the `definition` text gave +1.5 points (not significant) and raised stage-1 hits on the seven hardest tables from 0/7 to 3/7. The full "Scope and Usage" text, 13–23 times longer, gave −0.1 to −2.1 points at two to three times the latency. Matching every selected resource separately and keeping the one with the highest summed LLM confidence or coverage was 10.2–12.9 points worse than rank 1, because the model is confident in any resource it is given. On the first 15 tables, adding the source table name changed results by less than 2 points, and an Indonesian–English glossary hurt llm-full by 10–11 points (p = 0.03) without changing any stage-1 decision.

## 3.3 Error analysis

The largest failure is not linguistic. Almost every clinical Khanza table carries the visit number `no_rawat`, so stage 1 includes Encounter for 24 of 41 tables. When Encounter is part of the union target, the model maps the table onto Encounter instead of the resource that the table describes (Table 7). Tables that include Encounter are intrinsically harder (oracle 0.41 against 0.73), but the gap to the oracle still doubles. For the referral table `rujuk`, with ServiceRequest correctly selected, the model predicted `no_rujuk` → `Encounter.identifier` and `kd_dokter` → `Encounter.participant.individual` and scored 0 against an oracle of 0.62. Under the annotation convention every correspondence lies in one resource, and a foreign key such as `no_rawat` maps to `X.encounter`, which is why the primary variant works. The same absorption appears in confirm18 and persists with GLM, whose union variant gains nothing over llm-full.

Table 7 Effect of Encounter in the union target (31 dev41 tables whose correct resource is not Encounter but was selected)
| Encounter selected | Tables | Top predictions to Encounter | Top predictions to correct resource | R@|GT| | Oracle | Gap |
| no | 17 | 0% | 76% | 0.60 | 0.73 | 0.13 |
| yes | 14 | 63% | 30% | 0.13 | 0.41 | 0.28 |

A second failure concerns FHIR modelling knowledge. Referral and order tables (`rujuk`, `rujuk_masuk`, `rujukan_internal_poli`, `permintaan_lab`, `permintaan_radiologi`) were never assigned to ServiceRequest by Qwen's stage 1 with the `short` catalogue (0/5). A glossary that labelled the column `rujuk_ke (EN: refer to)` left every stage-1 decision unchanged, so the model understands the Indonesian term but not the convention that a referral is a FHIR ServiceRequest. The `definition` text, which mentions referrals, recovered three of the seven hardest tables, while the longer specification text did not help further. This is consistent with reports that both too little and too much context hurt LLM matching [@parciak] and with long-context degradation [@lostmiddle]. The section on ServiceRequest states that a request leads to a DiagnosticReport or Observation, and the 8B model then selected those resources; laboratory and radiology orders went to DiagnosticReport in every variant.

Third, a negative instruction that named the failure backfired. An instruction telling stage 1 not to rank first a resource that the table only references, which named Encounter, Patient and Practitioner as examples, raised wrong rank-1 choices of Encounter from 7 to 14 of 41 tables and lowered rank-1 accuracy from 26/41 to 23/41. Naming the resource to avoid made the model more likely to choose it, in line with known weaknesses of language models on negated prompts [@negated]. Finally, one held-out system uses generic column names (`id`, `nama`, `no_telepon`). Its tables cannot be told apart without the table name, and Qwen scores 0 in every non-oracle configuration against an oracle of 0.89; for such schemas the table name is likely decisive. With a perfect choice among the stage-1 candidates, dev41 would reach 0.508, only 4.4 points below the oracle, so the remaining gap is almost entirely a resource-selection problem.

These findings refine earlier observations in the literature. Parciak et al. reported that LLM matching quality suffers from both too little and too much context [@parciak]; our stage-1 results show the same trade-off for resource descriptions, where one definition paragraph helps and full specification sections do not. Retrieve-and-rerank designs [@rematch; @magneto] select candidate *elements* per column, and in our setting their ceiling is set by an off-the-shelf retriever that cannot read abbreviated Indonesian names (recall@10 0.40 on the large target); selecting the *resource* first uses the structure of the standard instead and avoids this ceiling. Finally, our result that a mined dictionary helps retrieval but not a capable LLM is consistent with the motivation of LLM-based expansion work [@nameguess; @columbo], which treats expansion as a pre-processing step for weaker downstream components.

## 3.4 Efficiency and practical use

Table 8 reports the cost per table on all 59 tables. Compared with llm-full, the primary variant needs 47% fewer prompt tokens and 5–20% fewer output tokens with both models. On the local 8B model, which processes prompts slowly, this also shortens the median time per table from 19.4 to 16.1 seconds. Through the API the situation is reversed: each call is fast, so the second sequential call dominates, and the primary variant takes 3.2 seconds against 2.0 for llm-full. The choice therefore depends on the deployment. A facility that runs a local model on modest hardware gains both accuracy and time, whereas an API user trades about one second per table for 11–13 points of recall and roughly half the token cost.

Table 8 Mean prompt and output tokens and median seconds per table (59 tables)
| Configuration | Qwen prompt | Qwen output | Qwen s | GLM prompt | GLM output | GLM s |
| llm-full | 1,918 | 342 | 19.4 | 1,914 | 333 | 2.0 |
| two-stage union | 1,287 | 395 | 17.1 | 1,153 | 326 | 3.3 |
| two-stage primary | 1,015 | 324 | 16.1 | 1,022 | 265 | 3.2 |
| oracle | 294 | 285 | 10.7 | 290 | 259 | 1.9 |

For integration practice, three observations follow from the results. First, the selected resource is a single, easily verified decision; asking an engineer to confirm or correct it before column matching removes most of the remaining gap at almost no cost, since the oracle is 8–18 points above the primary variant. Second, the matcher only sees names and types, so schemas with generic names such as `id` and `nama` should be matched together with the table name or a short table description. Third, an 8B model on a laptop is enough to produce a useful first draft of a mapping without sending any schema to an external service, which matters for hospitals whose policies restrict data transfer even for metadata.

## 3.5 Limitations

The gold standard was drafted by one annotator, and the conventions are design choices that another team could make differently [TBD: report agreement after adjudication]. The one-resource-per-table convention favours the primary variant; tables that genuinely populate several resources, such as a registration table that creates both a Patient and an Encounter, would be under-served, and the benchmark does not measure this. Per-pair differences have a standard deviation of about 0.28, so effects of 10 points need 120–200 tables for 80% power; the pre-registered test was underpowered. Each configuration was run once, and API decoding at temperature 0 is not guaranteed to be deterministic. The benchmark covers 11 of about 145 FHIR resources, uses names and types only, and is dominated by one system in the development set, and the held-out set has now been used. All source schemas and the FHIR specification are public and may appear in training data, although our annotations do not [@contamination].

# 4. CONCLUSIONS

Mapping the database of an Indonesian hospital or community health centre onto FHIR is hard for classic matchers and far from solved for LLMs. When the whole standard is the target, accuracy roughly halves, and most errors put the right attribute into the wrong resource. Choosing the resource first from the standard's own definitions and then matching only against that resource improves recall by 12.7–13.7 points at about half the prompt tokens, consistently for two open model families; on a pre-registered held-out set the improvement has the same size but is not statistically confirmed. The remaining errors concern how FHIR models a hospital, for example that a referral is a ServiceRequest and that a visit number is a reference, rather than Indonesian vocabulary or abbreviations. Resource selection is now the main bottleneck, and a single human confirmation of the selected resource is a cheap safeguard in practice.

# 5. FUTURE WORKS

Future work will enlarge the held-out set with more systems to reach adequate statistical power, measure the conditional effect of table names on schemas with generic columns, compare the mined dictionary with LLM-based abbreviation expansion [@columbo], and run the same tables in Indonesian, English and mixed variants to isolate the effect of language.

# ACKNOWLEDGEMENTS

[Optional: funding institution.]
