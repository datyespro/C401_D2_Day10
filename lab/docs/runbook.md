# Runbook — Lab Day 10: Stale Refund Window in Vector Store

**Incident Type:** Data Quality / Retrieval Correctness  
**Severity:** HIGH (MERIT tier check failure)  
**Component:** ETL → Clean → Embed → Retrieval Eval  
**Owner:** Embed Owner / Quality Owner  
**Last Updated:** 2026-04-15  

---

## 1. Symptom — Cơn đau

### What happened
Grading metric score `gq_d10_01` trả về **`hits_forbidden=true`** ❌
- Question: "Theo policy hoàn tiền nội bộ, khách có tối đa bao nhiêu ngày làm việc để gửi yêu cầu hoàn tiền?"
- Expected answer: **7 ngày làm việc** (chính sách hiện hành 2026)
- Problem: Top-k retrieval chunks vẫn chứa **deprecated content "14 ngày làm việc"** (policy-v3 cũ)

### User Impact
- LLM agent sẽ thấy context chứa dữ liệu không nhất quán (7 vs 14 ngày)
- → Có nguy cơ trả lời sai hoặc lưỡng lự
- → **MERIT ranking không đạt** (failure on correctness check)

### Example
```
Retrieval top-5:
1. chunk_id=policy_refund_v4_1: "Yêu cầu... 7 ngày làm việc" ✅
2. chunk_id=policy_refund_v4_2: "Yêu cầu hoàn tiền... 14 ngày làm việc [sync cũ]" ❌ ← FORBIDDEN
3. chunk_id=policy_refund_v4_3: "Yêu cầu... 7 ngày làm việc"  ✅
```

---

## 2. Detection — Phát hiện ngay

### Metrics to monitor
| Metric | Expected | Actual | Alert |
|--------|----------|--------|-------|
| **grading.gq_d10_01.hits_forbidden** | false | true | 🚨 FAIL |
| **grading.gq_d10_01.contains_expected** | true | true | ✅ OK |
| **expectation.refund_no_stale_14d_window** | violations=0 | violations=0 | ✅ OK (cleaned) |
| **embed.prune_removed** | ≥1 | 0 (before fix) | ⚠️ WARN |

### How to detect
```bash
# 1. Check grading result immediate
tail -1 artifacts/eval/grading_run.jsonl | grep gq_d10_01
# Look for: "hits_forbidden": true → ALERT

# 2. Run grading validation
python instructor_quick_check.py --grading artifacts/eval/grading_run.jsonl
# Output MERIT_CHECK[gq_d10_01] FAIL = immediate action needed
```

---

## 3. Diagnosis — Chẩn đoán chi tiết (5 bước)

### Step 1: Verify cleaned data
```bash
# Check if cleaning rules removed stale chunks
grep -i "14 ngày" artifacts/cleaned/cleaned_*.csv
# Result: Should be EMPTY (not found)
# If found → Cleaning rule failed
```

### Step 2: Check quarantine separation
```bash
# Verify old policy chunks were quarantined
grep -c "14 ngày" artifacts/quarantine/quarantine_*.csv
# Expected: >0 (quarantined successfully)
# If 0 → No quarantine, chunks leaked into cleaned
```

### Step 3: Inspect Chroma collection
```bash
# Query vector store for stale content
python -c "
import chromadb
client = chromadb.PersistentClient(path='chroma_db')
col = client.get_collection('day10_kb')

# Search for forbidden text
results = col.query(query_texts=['14 ngày làm việc'], n_results=5)
print('Stale chunks in Chroma:')
for i, doc in enumerate(results['documents'][0]):
    print(f'{i+1}. {doc[:80]}...')

# Count collection size
print(f'Total chunks: {col.count()}')
"
# Expected: NO "14 ngày" results
# If found → Vector store was not pruned after cleaning
```

### Step 4: Check manifest prune record
```bash
# Inspect the last run's manifest
python -c "
import json
manifest = json.load(open('artifacts/manifests/manifest_<LAST_RUN_ID>.json'))
print(f\"Cleaned records: {manifest['cleaned_records']}\")
print(f\"Embed upsert: {manifest['embed_upsert_count']}\")
print(f\"Embed prune removed: {manifest.get('embed_prune_removed', 'N/A')}\")
"
# Expected: embed_prune_removed ≥ 1 (old vectors deleted)
# If 0 → No pruning happened = root cause
```

### Step 5: Run eval retrieval before-state
```bash
# Capture current retrieval quality
python eval_retrieval.py --out artifacts/eval/before_fix_eval.csv --top-k 5

# Check hits_forbidden count
python -c "
import pandas as pd
df = pd.read_csv('artifacts/eval/before_fix_eval.csv')
fails = df[df['hits_forbidden'] == True]
print(f'Queries with forbidden chunks: {len(fails)}/{len(df)}')
print(fails[['question_id', 'hits_forbidden']])
"
# Expected: At least gq_d10_01 should show hits_forbidden=True
```

### Diagnosis Summary
```
✅ Cleaned: No "14 ngày" in cleaned CSV
✅ Quarantine: "14 ngày" found (properly separated)
❌ Chroma: "14 ngày" STILL present
❌ Manifest: embed_prune_removed = 0
❌ Eval: hits_forbidden = True

→ ROOT CAUSE: Vector store not pruned after previous cleaning run
→ ACTION: Need full reindex with prune enabled
```

---

## 4. Mitigation — Xử lý ngay lập tức

### Option 1: RECOMMENDED — Full reindex (cleanup-refund pattern)
```bash
# Step 1: Rerun pipeline with explicit run_id
python etl_pipeline.py run --run-id cleanup-refund

# Expected output:
# - embed_prune_removed=1 (old vectors deleted)
# - expectation[refund_no_stale_14d_window] OK (violations=0)
# - manifest_written=artifacts/manifests/manifest_cleanup-refund.json

# Step 2: Verify manifest
cat artifacts/manifests/manifest_cleanup-refund.json | grep embed_prune_removed
# Should output: "embed_prune_removed": 1 ✅
```

### Option 2: Manual Chroma prune (if pipeline restart not possible)
```bash
python etl_pipeline.py validate-only \
  --manifest artifacts/manifests/manifest_cleanup-refund.json \
  --prune-old-vectors
```

### Option 3: Rollback (emergency only)
```bash
# Restore from previous good state
git log --oneline chroma_db/
# Restore point before bad commit
git checkout <good-commit> -- chroma_db/
```

### Verification after mitigation
```bash
# Re-run grading immediately
python grading_run.py --out artifacts/eval/grading_run_fixed.jsonl

# Check if gq_d10_01 now has hits_forbidden=false
python instructor_quick_check.py --grading artifacts/eval/grading_run_fixed.jsonl

# Expected:
# MERIT_CHECK[gq_d10_01] OK :: refund window + không forbidden trong top-k ✅
```

---

## 5. Prevention — Phòng chống dài hạn

### 1️⃣ Automated grading pre-production check
```yaml
# Add to CI/CD pipeline
pre_deploy_test:
  script:
    - python grading_run.py --out /tmp/grading_test.jsonl
    - python instructor_quick_check.py --grading /tmp/grading_test.jsonl
    - if any hits_forbidden=true; then exit 1; fi
  on_failure: "Halt deployment, alert team"
```

### 2️⃣ Monitor embed prune metric
```bash
# Add to monitoring dashboard
expectation: embed_prune_removed > 0 after each run
alert: if embed_prune_removed = 0 on production → P2 incident
```

### 3️⃣ Collection health check (monthly)
```bash
python -c "
# Detect zombie vectors (in store but not in manifest)
import chromadb
client = chromadb.PersistentClient(path='chroma_db')
col = client.get_collection('day10_kb')

# Get all doc_ids from Chroma
chroma_docs = set(col.get()['ids'])

# Get expected doc_ids from latest manifest
# If diff > threshold → alert
print(f'Unexpected vectors: {len(chroma_docs) - expected_count}')
"
```

### 4️⃣ Version control for policy windows
```yaml
# data_contract.yaml
policies:
  refund_window_days: 7  # ← Read from contract, don't hard-code
  effective_from: "2026-02-01"
  deprecated_versions:
    - window_days: 14
      effective_until: "2026-02-01"  # ← Quarantine after this date
```

### 5️⃣ Freshness watermark lag alert
```bash
# Add watermark tracking
freshness_check:
  watermark: 2026-04-10T08:00:00  # Latest data
  lag_hours: 122 (FAIL > 24h SLA)
  action: "Alert if lag > 24h; escalate if > 48h"
```

---

## 6. Freshness FAIL — Giải thích SLA

### Current Status
```
freshness_check = FAIL ❌
Reasons:
  - latest_exported_at: 2026-04-10T08:00:00 (5 days old)
  - age_hours: 122.27 > SLA_24h
  - watermark_lag_hours_threshold: 2.0 (exceeded)
```

### Why FAIL is expected on lab
- CSV mẫu (policy_export_dirty.csv) có snapshot cũ từ 2026-04-10
- Lab SLA = 24 giờ (simulation)
- Dữ liệu thực tế: 122 giờ → **Legitimately stale data**

### Production interpretation
- **FAIL ≠ Pipeline bug** (data is legitimately old)
- **FAIL = Alert dân IT ops**: "Data snapshot needs refresh"
- **Action**: Re-export từ source system hoặc update exported_at field

### How to resolve (for lab)
```bash
# Option 1: Update timestamp to current (if OK by instructor)
sed -i 's/2026-04-10T08:00:00/2026-04-15T10:00:00/g' \
  data/raw/policy_export_dirty.csv

python etl_pipeline.py run --run-id test-freshness
# → freshness_check = PASS ✅

# Option 2: Adjust SLA in contract
# data_contract.yaml:
#   freshness_sla_hours: 144  # 6 days instead of 24

# Option 3: Document as known limitation
# docs/runbook.md: "Lab snapshot is intentionally stale to simulate
# data age scenarios"
```

---

## 7. Evidence — Chứng cứ & liên kết

### Manifest trail (before → after)
```
Before fix:
  artifacts/manifests/manifest_ci-smoke2.json
    ├─ cleaned_records: 6
    ├─ quarantine_records: 4
    └─ embed_prune_removed: 0 ❌

After fix:
  artifacts/manifests/manifest_cleanup-refund.json
    ├─ cleaned_records: 6
    ├─ quarantine_records: 4
    └─ embed_prune_removed: 1 ✅
```

### Grading results
```
Before: gq_d10_01 :: contains_expected=true, hits_forbidden=true ❌
After:  gq_d10_01 :: contains_expected=true, hits_forbidden=false ✅
```

### Relevant files
- CSV cleaned: artifacts/cleaned/cleaned_cleanup-refund.csv (6 rows, no stale)
- CSV quarantine: artifacts/quarantine/quarantine_cleanup-refund.csv (4 rows, includes old policy)
- Grading log: artifacts/eval/grading_run.jsonl (3 metrics, all PASS)
- Group report: reports/group_report.md (Section 3b details this incident)

---

## 8. Timeline & Owner

| Time | Event | Owner | Status |
|------|-------|-------|--------|
| 2026-04-15 14:30 | Grading iteration 1 discovers hits_forbidden=true | Quality Owner | 🚨 DETECTED |
| 2026-04-15 14:35 | Diagnosis: Vector store not pruned | Embed Owner | 📊 ROOT CAUSE FOUND |
| 2026-04-15 14:45 | Rerun pipeline --run-id cleanup-refund | Embed Owner | ✅ MITIGATED |
| 2026-04-15 14:50 | Regenerate grading, verify MERIT pass | Quality Owner | ✅ VERIFIED |
| 2026-04-15 15:00 | Update group report + this runbook | Docs Owner | ✅ DOCUMENTED |
| 2026-04-15 18:00 | Submit with MERIT ranking | All | 🎉 COMPLETE |

---

## Q&A

**Q: Tại sao expectation pass nhưng vector store vẫn chứa chunk cũ?**  
A: Expectation kiểm tra cleaned data (đúng), nhưng không enforce xoá vector cũ khỏi Chroma → cần `embed_prune_removed > 0`.

**Q: Nếu CI không đủ GPU để reindex?**  
A: Chạy trên CPU (SentenceTransformers hỗ trợ CPU). Nếu timeout, manual reindex local rồi push vector snapshot.

**Q: Incident này có ảnh hưởng tới Day 09 agent không?**  
A: Có, nếu Day 09 query sang `day10_kb`. Fix runbook này đảm bảo `day10_kb` sạch khi integrate.
# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

> User / agent thấy gì? Khi inject policy_export_dirty, agent retrieve chunk có chứa nội dung "Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày làm việc kể từ xác nhận đơn " Trong khi đó số ngày thực tế là 7 ngày làm việc. Điều này có thể dẫn đến việc agent đưa ra câu trả lời sai.

---

## Detection

> Metric nào báo? eval 'hit_forbidens'

---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Kiểm tra `artifacts/manifests/*.json` | quarantine records = 5 |
| 2 | Mở `artifacts/quarantine/*.csv` |Có chunk "Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày làm việc kể từ xác nhận đơn" |
| 3 | Chạy `python eval_retrieval.py` | hit_forbiden = 'no' |

---

## Mitigation

> Rerun pipeline, rollback embed, tạm banner “data stale”

---

## Prevention

> Thêm expectation, alert, owner, watermark lag, clockskew
