Feature: Measurement
  The working data sits in SQL; the schema and seed run in sqlite3 as they do
  in the browser.

  Background:
    Given the database built from the schema and the seed

  @S-26 @R-44
  Scenario: Every run has twelve rows per document
    Then every run and document has 12 extraction rows

  @S-27 @R-45
  Scenario: The baseline states its basis and is NULL where not measured
    Then every baseline row has a basis of "assumed", "measured" or "not measured"
    And the baseline "discrepancies_per_paper" is NULL with basis "not measured"

  @S-28 @R-47 @R-49 @R-75 @R-76
  Scenario: Against the baseline, one row per metric, each with its basis
    When query "4_time_saved_against_baseline" runs
    Then it returns 4 rows
    And the row "minutes_per_contract" has a negative change and basis "assumed"
    And the row "discrepancies_per_paper" has NULL before

  @S-29 @R-48
  Scenario: No committee date is invented
    When query "2_cycle_time_to_committee" runs
    Then "Havrebakke Wind Farm" has 21.0 days to committee
    And "Lichtung Offshore" has NULL days to committee

  @S-30 @R-46 @R-47
  Scenario: The extracted figures can be asked across contracts
    When query "5_a_portfolio_question" runs
    Then "havrebakke-ppa-v2-execution" has curtailment cap 150 hours
    And "olivos-solar-ppa-execution" has NULL curtailment cap
    And "olivos-solar-ppa-execution" has price 38.75

  @S-31 @R-47 @R-75 @R-77
  Scenario: Effort per contract counts the two decisions and the minutes
    When query "1_review_effort_per_contract" runs
    Then it returns 4 rows
    And the columns include "confirmed", "flagged" and "review_minutes"
    And "lichtung-offshore-ppa-execution" has 9 confirmed and 3 flagged
    And every review outcome is "confirmed" or "flagged"

  @S-32 @R-78
  Scenario: The findings per term come from the checks table
    When query "3_terms_that_need_a_human" runs
    Then it returns 12 rows
    And the columns include "flagged" and "check_findings"
    And the term "Events of default, termination and termination amount" has at least 1 check finding

  @S-88 @R-94
  Scenario: A second decision on a term is a new row, and the later one counts
    When a second decision "flagged" is added on the term "5_price_and_indexation" of "olivos-solar-ppa-execution"
    Then the reviews table holds 2 rows for the term "5_price_and_indexation" of "olivos-solar-ppa-execution"
    When query "1_review_effort_per_contract" runs
    Then "olivos-solar-ppa-execution" has 11 confirmed and 1 flagged

  @S-33 @R-75 @pending
  Scenario: Analyst minutes are timed from load to the last decision
    The generated log holds fixed minutes per term; the screen counts minutes
    since the first decision but does not store them. Timing per case is the
    pilot's first measurement.
    Given a case loaded and reviewed on the screen
    Then the minutes from load to the last decision are stored in the reviews table

  @S-34 @R-76 @pending
  Scenario: Days to a reviewed table are dated from the data-room event to the last decision
    The events table carries the documents' own dates, offset by rule; no real
    data-room event exists yet.
    Given a project with a data-room event and a reviewed table
    Then the days between them are stored and reported in the cycle-time query

  @S-81 @R-77 @pending
  Scenario: The confirmed and flagged counts come from decisions stored beyond the browser tab
    The prototype keeps decisions in the tab and the database holds a generated log.
    Given a reviewed contract whose decisions are stored in the reviews table
    Then the effort query counts its confirmed and flagged terms from those rows

  @S-35 @R-79 @pending
  Scenario: Model cost per contract is recorded with the extraction
    The run records carry no token counts; the extractor must store tokens and
    price per document before this can be reported.
    Given a recorded run with tokens and price per document
    Then the cost per contract is reported beside the minutes per contract

  @S-36 @R-80 @pending
  Scenario: The operational error rate is measured monthly and stored with basis measured
    No real contract has been read; the sample re-read by a person does not exist yet.
    Given a month of extractions and a re-read sample
    Then the share found wrong is stored in the baseline table with basis "measured"
