# Application assurance and reproducibility

This repository is a research prototype, **not a clinical system**.

## Evidence tiers

1. **Historical MRI experiments:** the manuscript reports BraTS 2021 five-fold results and UCSF-PDGM/UPenn-GBM transfer scores. Existing source-subject overlap means that these are not independent external-validation results.
2. **Bounded mathematical verification:** an UNSAT result holds only for the encoded property over the represented latent region. SAT may reflect an abstract counterexample requiring reachability analysis. TIMEOUT proves neither validity nor violation.
3. **Workflow status logic:** TLA+ is used for release-status handling, not for model accuracy, MRI acquisition safety, or medical claims.
4. **Reference-policy unit tests:** `tests/test_release_contract.py` provides six executable tests for the separate reference release-policy function. These tests do **not** exercise the deployed web application's handlers or validate the reported clinical-imaging experiments.

## Run the reference-policy tests

```bash
python -m unittest discover -s tests -p 'test_release_contract.py' -v
```

## Needed for independent replication

- Original training checkpoint and numerical symbolic-loss coefficient
- Complete fold assignment manifest and subject-level out-of-fold predictions
- Deduplicated cross-cohort identifiers and independently disjoint validation cohort
- Latent-region/property-to-subject manifest, concrete solver inputs and logs
- TLC console logs with state counts and a reproducible command
- Clinical expert review of the seven rules
- Integration tests that send real requests through the deployed API and validate the downloadable report

**Do not describe the six reference-policy tests as end-to-end software testing.** The repository's demo/surrogate mode must never be interpreted as producing paper checkpoint predictions.
