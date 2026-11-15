-- 3. Where the method needs a human: per term, how often the model's answer stood across runs,
--    how often the analyst flagged it, and how many deterministic checks fired on it.
WITH current AS (                          -- the current decision per term: the latest row of the append-only log (R-94)
  SELECT r.* FROM reviews r
  WHERE r.decided_at = (SELECT MAX(r2.decided_at) FROM reviews r2
                        WHERE r2.document_id = r.document_id AND r2.document_sha256 = r.document_sha256 AND r2.term_id = r.term_id)
)
SELECT t.ord,
       t.label                                                               AS term,
       COUNT(DISTINCT e.run)                                                 AS runs,
       ROUND(100.0 * SUM(e.verdict IN ('correct','faithful')) / COUNT(*))   AS model_right_pct,
       (SELECT COUNT(*) FROM current r WHERE r.term_id = t.id AND r.outcome = 'flagged')   AS flagged,
       (SELECT COUNT(*) FROM checks c WHERE c.term_id = t.id)                AS check_findings
FROM terms t
JOIN extractions e ON e.term_id = t.id
JOIN documents  d ON d.id = e.document_id AND d.kind IN ('ppa_execution','ppa_draft')
GROUP BY t.id
ORDER BY model_right_pct ASC, flagged DESC, t.ord;
