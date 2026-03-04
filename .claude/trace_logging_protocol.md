## 6. Trace Logging Protocol

Every analysis run MUST have a `run_id` (format: `YYYYMMDD_HHMMSS_<short_description>`).

### Session start (mandatory)
```bash
python scripts/trace_logger.py init-run \
  --run-id $(date +%Y%m%d_%H%M%S)_<short_description> \
  --project-dir <project_dir> \
  --task-description "<one sentence>"
```

### Mandatory logging calls

| Event | Command | When |
|-------|---------|------|
| Sequential thinking | `log-sequential` | Before every ST invocation |
| Biomni query | `log-biomni` | After every query that informs a decision |
| Method/tool selection | `log-decision` | At every model, tool, or QC threshold choice |
| Plan finalized | `log-decision --phase planning` | Before ExitPlanMode |

These are non-negotiable. A run without a trace has no audit trail.

### Command patterns
```bash
# Sequential thinking
python scripts/trace_logger.py log-sequential \
  --run-id $RUN_ID --project-dir $PROJECT_DIR \
  --trigger "≥2 competing hypotheses" \
  --context "<ambiguity description>" \
  --hypotheses "hyp_a,hyp_b" \
  --evidence-used "<what was checked>" \
  --branch-closed "hyp_b" \
  --conclusion "<final decision>"

# Decision
python scripts/trace_logger.py log-decision \
  --run-id $RUN_ID --project-dir $PROJECT_DIR \
  --phase planning \
  --decision "<what was chosen>" \
  --rationale "<why>" \
  --alternatives-considered "alt1,alt2"

# Biomni query
python scripts/trace_logger.py log-biomni \
  --run-id $RUN_ID --project-dir $PROJECT_DIR \
  --query "<query text>" \
  --tool-used "<tool>" \
  --summary "<result summary>" \
  --downstream-decision "<decision informed>"

# Summarize at session end
python scripts/trace_logger.py summarize \
  --run-id $RUN_ID --project-dir $PROJECT_DIR
```
