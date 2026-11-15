-- 5. A portfolio question on the extracted terms: once the twelve terms are structured,
--    the figures in them can be asked across contracts. Here: the price, the supply
--    period, the curtailment cap and the delay-damages cap, per contract, from run 1.
--    Limit: the facts table stores a figure and its unit, not what the figure means. MAX(hours)
--    returns the cap here only because the cap is the largest hour figure in the term; the next
--    step is a fact kind per figure (curtailment_cap_hours, notice_hours), stored at extraction.
SELECT d.id                                                                        AS contract,
       p.technology,
       MAX(CASE WHEN f.term_id = '5_price_and_indexation' AND f.unit = 'eur_per_mwh' THEN CAST(f.value AS REAL) END) AS price_eur_per_mwh,
       MAX(CASE WHEN f.term_id = '3_supply_period'  AND f.unit = 'years'  THEN CAST(f.value AS INTEGER) END) AS supply_years,
       MAX(CASE WHEN f.term_id = '8_curtailment'    AND f.unit = 'hours'  THEN CAST(f.value AS INTEGER) END) AS curtailment_cap_hours,
       MAX(CASE WHEN f.term_id = '4_cod_and_delay'  AND f.unit = 'eur'    THEN CAST(f.value AS REAL)    END) AS delay_damages_cap_eur
FROM documents d
JOIN projects p ON p.id = d.project_id
LEFT JOIN facts f ON f.document_id = d.id AND f.run = 1
WHERE d.kind IN ('ppa_execution','ppa_draft')
GROUP BY d.id
ORDER BY d.version_date;
