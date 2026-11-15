Feature: Continuous evaluation
  The score is kept honest after the first run. Scenarios tagged @pending are
  specified and not yet built; they are reported as pending, never as passed.

  @S-37 @R-64 @R-18
  Scenario: Every recorded run is scored and shown, not only the best
    Given the recorded runs
    Then the evaluation reports a summary for every run directory
    And no run is left out of the stability count

  @S-38 @R-58 @R-59
  Scenario: A term wrong in every run is a definition defect, a term wrong in some runs is routed to a check or a reviewer
    Given the recorded runs
    Then "12_change_in_law_and_force_majeure" of "lichtung-offshore-ppa-execution" is wrong in every run
    And the term definition of "12_change_in_law_and_force_majeure" does not ask for the reference price fallback
    And "7_product_and_certificates" of "lichtung-offshore-ppa-execution" is wrong in some runs

  @S-39 @R-57
  Scenario: Stability rests on at least three runs
    Given the recorded runs
    Then at least 3 runs are recorded for the current model

  @S-40 @R-54 @pending
  Scenario: The key is versioned and the evaluation records the version
    Given the recorded runs
    Then every key entry carries a date
    And the evaluation records the key version it scored against

  @S-41 @R-55 @R-56 @pending
  Scenario: A change to the prompt is scored against the previous run before use
    Given a new run after a change to the term definitions
    When it is scored against the previous run
    Then every term is reported as improved, regressed or unchanged
    And a regression from correct blocks the change until a reason is written

  @S-42 @R-60 @pending
  Scenario: A reviewer's flag becomes a candidate change to the key
    The screen keeps flags in the browser tab; nothing writes them to the key.
    Given the reviewer flags a term on the screen with a note
    Then the flag and its note are stored as a candidate key change with reviewer and date

  @S-79 @R-60a @pending
  Scenario: A reviewed contract enters the suite only through a key written blind
    Given a contract the reviewer has confirmed on the screen, term by term
    Then it is not in the suite until a person has keyed it without the extraction in view, and the key names that person and the date

  @S-43 @R-61 @pending
  Scenario: Scored on a real contract before real use
    Given a real contract of comparable length with a key written by a person
    Then its score is reported beside the synthetic score

  @S-76 @R-61a @pending
  Scenario: The suite covers the pipeline, and says where it does not
    Given the contract forms, counterparty types and languages in the pipeline
    Then the evaluation report lists each one with its keyed contracts, and names those with none

  @S-44 @R-62 @pending
  Scenario: An operational error rate is measured monthly
    Given a month of extractions in operation
    When a sample is re-read by a person
    Then the share found wrong is recorded and shown beside the synthetic score

  @S-45 @R-63 @pending
  Scenario: Cost per contract is recorded with every run
    Given a recorded run
    Then every record carries tokens and price, and business case v2 shows cost per contract

  @S-78 @R-63a @pending
  Scenario: A model judges the wording of a term only after calibration against a person
    Given a term whose value is wording, and a sample judged by a person who read the contract
    Then the model's judgments count in the score only after their agreement with the person's is measured, and that rate is shown beside the score
