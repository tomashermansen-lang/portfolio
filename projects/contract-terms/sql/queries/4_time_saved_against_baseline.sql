-- 4. Against the baseline: before, after and the change per metric (after minus before), and on what basis the baseline rests.
--    The baseline rows are assumptions until the first weeks in the seat replace them with measurements.
WITH current AS (                          -- the current decision per term: the latest row of the append-only log (R-94)
  SELECT r.* FROM reviews r
  WHERE r.decided_at = (SELECT MAX(r2.decided_at) FROM reviews r2
                        WHERE r2.document_id = r.document_id AND r2.document_sha256 = r.document_sha256 AND r2.term_id = r.term_id)
),
measured AS (
  SELECT 'minutes_per_contract' AS metric,
         (SELECT AVG(m) FROM (SELECT SUM(minutes) AS m FROM current GROUP BY document_id)) AS value
  UNION ALL
  SELECT 'days_to_reviewed_table',
         (SELECT AVG(julianday(r.at) - julianday(d.at))
            FROM events d JOIN events r ON r.project_id = d.project_id
           WHERE d.event = 'dataroom_received' AND r.event = 'terms_reviewed')
  UNION ALL
  SELECT 'discrepancies_per_paper',
         (SELECT 1.0 * COUNT(*) FROM checks WHERE check_name = 'paper_vs_contract')
         / (SELECT COUNT(*) FROM documents WHERE kind IN ('dd_summary','ic_paper'))
  UNION ALL
  SELECT 'contracts_processed',
         (SELECT COUNT(DISTINCT document_id) FROM current)
)
SELECT b.metric,
       b.unit,
       b.value                                   AS before,
       ROUND(m.value, 1)                         AS after,
       CASE WHEN b.value IS NULL THEN NULL ELSE ROUND(m.value - b.value, 1) END AS change,
       b.basis                                   AS before_basis,
       b.source
FROM baseline b LEFT JOIN measured m ON m.metric = b.metric
ORDER BY CASE b.metric WHEN 'minutes_per_contract' THEN 1 WHEN 'days_to_reviewed_table' THEN 2 WHEN 'discrepancies_per_paper' THEN 3 ELSE 4 END;
