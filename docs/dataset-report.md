# Dataset inspection report

Both supplied files were read without changing their contents. Initial inspection identified:

| Dataset | Records | Fields | Labels |
|---|---:|---|---|
| `phishing_cleaned.csv` | 53,449 | subject, sender, receiver, body, urls, date, label | 27,530 phishing (`1`); 25,919 safe (`0`) |
| `spam.csv` | 5,572 | Category, Message | 747 spam; 4,825 ham |

The pipeline uses subject, sender, body, and the supplied URL column from the phishing email file. It uses Message from the SMS corpus. The categories `spam` and label `1` map to phishing; `ham` and label `0` map to safe. This mapping is a common binary educational task but spam messages are not all phishing and are shorter than email, so the model's real-world generalization is limited.

The inspected files contain no unusable or unlabeled records. `phishing_cleaned.csv` has 23,520 missing cells (mostly optional metadata), zero exact duplicate rows, and 53,449 usable labeled messages. `spam.csv` has no missing cells, 416 exact duplicate rows, and 5,572 labeled nonempty messages. The loader records file schemas, row counts, missing cells, whole-row duplicate counts, usable labeled nonempty rows, and normalized class counts on each run. It skips unsupported schemas, drops unlabeled or empty-text rows, normalizes text and removes HTML markup, deduplicates exact text across sources, and keeps the original CSVs intact. After cross-source text deduplication, 477 records were removed and 58,544 unique examples remained; 46,835 went to training and 11,709 to the stratified test split.

Training writes a distinct `python-ml-service/data/processed/combined_emails.csv` with normalized text, binary label, and source filename. This file is generated from both datasets and is excluded from version control; the originals are never modified.
