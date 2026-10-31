-- 1. Effort per contract: what the analyst's pass cost, and how much of the table stood first time.
WITH current AS (                          -- the current decision per term: the latest row of the append-only log (R-94)
  SELECT r.* FROM reviews r
  WHERE r.decided_at = (SELECT MAX(r2.decided_at) FROM reviews r2
                        WHERE r2.document_id = r.document_id AND r2.document_sha256 = r.document_sha256 AND r2.term_id = r.term_id)
)
SELECT d.id                                              AS document,
       p.name                                            AS project,
       COUNT(*)                                          AS terms,
       SUM(r.outcome = 'confirmed')                      AS confirmed,
       SUM(r.outcome = 'flagged')                        AS flagged,
       ROUND(100.0 * SUM(r.outcome = 'confirmed') / COUNT(*)) AS first_pass_pct,
       ROUND(SUM(r.minutes), 1)                          AS review_minutes
FROM current r
JOIN documents d ON d.id = r.document_id
JOIN projects  p ON p.id = d.project_id
WHERE d.kind IN ('ppa_execution','ppa_draft')
GROUP BY d.id
ORDER BY review_minutes DESC;
