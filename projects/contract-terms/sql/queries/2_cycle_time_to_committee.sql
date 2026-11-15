-- 2. Cycle time: days from the data room to a reviewed terms table, and to the committee.
SELECT p.name                                                             AS project,
       MIN(CASE WHEN e.event = 'dataroom_received'  THEN e.at END)        AS dataroom_received,
       ROUND(julianday(MIN(CASE WHEN e.event = 'terms_reviewed' THEN e.at END))
           - julianday(MIN(CASE WHEN e.event = 'dataroom_received' THEN e.at END)), 1) AS days_to_reviewed_table,
       ROUND(julianday(MIN(CASE WHEN e.event = 'ic_meeting' THEN e.at END))
           - julianday(MIN(CASE WHEN e.event = 'dataroom_received' THEN e.at END)), 1) AS days_to_committee
FROM events e
JOIN projects p ON p.id = e.project_id
GROUP BY p.id
ORDER BY days_to_committee;
