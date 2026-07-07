# Data Provenance and Licence

## Overview

The `data/` directory contains two categories of content:

1. **SIMD v1.0** — original synthetic content (KG seed + 5 core manual files), released CC0
2. **Real public dataset reference files** — two new files summarising publicly available
   industrial fault datasets, included under their respective open licences

---

## Category 1: Synthetic Industrial Maintenance Dataset (SIMD) v1.0

**Files:**
- `data/kg_seed.cypher`
- `data/manuals/bearing_wear.txt`
- `data/manuals/cavitation.txt`
- `data/manuals/misalignment.txt`
- `data/manuals/seal_leakage.txt`
- `data/manuals/vibration_diagnostics_general.txt`

All SIMD v1.0 files are **original content authored by Vinita Silaparasetty (Aevoxis Solutions)**
and are dedicated to the public domain under the **Creative Commons CC0 1.0 Universal** licence.

### What SIMD v1.0 is

Original text authored for this experiment. Equipment names (Pump-14, Motor-03, etc.),
component part numbers, and facility identifiers are entirely fictitious. Fault descriptions,
symptom lists, and maintenance procedures reflect general engineering practice consistent
with publicly available standards (ISO 13306, ISO 10816-3, HI 9.6.1).

### What the technical content is informed by

The technical specifications in the five manual files are informed by the following real
public sources (cited in each file's SOURCE header):

| File | Real sources consulted |
|------|----------------------|
| `bearing_wear.txt` | CWRU Bearing Data Center; Wikipedia "Bearing (mechanical)" CC BY-SA 4.0; ISO 10816-3 |
| `cavitation.txt` | Wikipedia "Cavitation" CC BY-SA 4.0; HI 9.6.1 public summary; UCI Hydraulic Dataset CC BY 4.0 |
| `misalignment.txt` | Wikipedia "Shaft alignment" CC BY-SA 4.0; ISO 10816-3; ISO 13306 |
| `seal_leakage.txt` | Wikipedia "Mechanical seal" CC BY-SA 4.0; ISO 13306; UCI Hydraulic Dataset CC BY 4.0 |
| `vibration_diagnostics_general.txt` | ISO 10816-3; CWRU Bearing Data Center; Wikipedia "Vibration" CC BY-SA 4.0 |

### CC0 Licence text

To the extent possible under law, Vinita Silaparasetty has waived all copyright and
related or neighbouring rights to SIMD v1.0. This work is published from Ireland.

Full legal text: https://creativecommons.org/publicdomain/zero/1.0/

---

## Category 2: Real Public Dataset Reference Files

These two files summarise publicly available industrial fault benchmark datasets and are
included to ground the RAG corpus in verifiable, real-world fault signatures. They are
not synthetic — their content is derived from publicly documented dataset specifications.

### 2a. CWRU Bearing Data Center Reference

**File:** `data/manuals/cwru_bearing_signatures.txt`  
**Source:** Case Western Reserve University Bearing Data Center  
**URL:** https://engineering.case.edu/bearingdatacenter  
**Long-term mirror (Zenodo):** https://zenodo.org/records/10987113  
**Zenodo mirror licence:** Creative Commons Attribution 4.0 International (CC BY 4.0)  
**Usage terms:** Freely available for academic and research use. No explicit copyright
restriction stated by CWRU. Mirror re-uploaded to Zenodo under CC BY 4.0.

**What this file contains:**  
Bearing specifications (SKF 6205-2RS, 6203-2RS), documented characteristic fault frequency
multiples (BPFO = 3.585×, BPFI = 5.415× shaft frequency for drive-end bearing), fault
size documentation (0.007"–0.040" EDM pits), and mapping of CWRU fault classes to the
KG fault taxonomy (all three fault locations → Bearing Wear, F-BW-01).

**Canonical citation:**
> Smith, W. A., & Randall, R. B. (2015). Rolling element bearing diagnostics using the
> Case Western Reserve University data: A benchmark study. *Mechanical Systems and Signal
> Processing*, 64–65, 100–131. https://doi.org/10.1016/j.ymssp.2015.04.021

---

### 2b. UCI Condition Monitoring of Hydraulic Systems Reference

**File:** `data/manuals/uci_hydraulic_reference.txt`  
**Source:** UCI Machine Learning Repository  
**URL:** https://archive.ics.uci.edu/dataset/447/condition+monitoring+of+hydraulic+systems  
**DOI:** https://doi.org/10.24432/C5CW26  
**Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0) — free to use,
share, and adapt with attribution.

**What this file contains:**  
Sensor channel descriptions (17 sensors: pressure, flow, temperature, vibration, power),
fault types with graded severity (pump internal leakage, valve condition, cooler efficiency,
accumulator pressure), observable diagnostic signatures, and mapping to KG fault types
(Seal Leakage F-SL-03, Valve Seat Erosion F-VS-10, Actuator Sticking F-AS-09).

**Canonical citation:**
> Helwig, N., Pignanelli, E., & Schütze, A. (2015). Condition monitoring of a complex
> hydraulic system using multivariate statistics. In *Proceedings of IEEE International
> Instrumentation and Measurement Technology Conference (I2MTC)*, 210–215.
> https://doi.org/10.1109/I2MTC.2015.7151267

---

## Summary Table

| File | Type | Licence | Author/Source |
|------|------|---------|---------------|
| `kg_seed.cypher` | Synthetic | CC0 1.0 | Vinita Silaparasetty |
| `manuals/bearing_wear.txt` | Synthetic + real citations | CC0 1.0 | Vinita Silaparasetty |
| `manuals/cavitation.txt` | Synthetic + real citations | CC0 1.0 | Vinita Silaparasetty |
| `manuals/misalignment.txt` | Synthetic + real citations | CC0 1.0 | Vinita Silaparasetty |
| `manuals/seal_leakage.txt` | Synthetic + real citations | CC0 1.0 | Vinita Silaparasetty |
| `manuals/vibration_diagnostics_general.txt` | Synthetic + real citations | CC0 1.0 | Vinita Silaparasetty |
| `manuals/cwru_bearing_signatures.txt` | Real public data reference | Free academic use / CC BY 4.0 (Zenodo mirror) | CWRU |
| `manuals/uci_hydraulic_reference.txt` | Real public data reference | CC BY 4.0 | Helwig et al. / UCI |
