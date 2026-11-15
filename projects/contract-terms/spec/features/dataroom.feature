Feature: The data room
  Six synthetic documents, each held to its answer key by a validator that
  runs on the desk.

  @S-08 @R-03 @R-04
  Scenario: Every document passes the validator
    Then every document in the data room carries the synthetic header line
    And the validator reports no failure on any document

  @S-09 @R-05
  Scenario: A document that breaks a rule is reported with the rule
    When the header line is removed from a copy of "havrebakke-ppa-v2-execution"
    Then the validator reports "header line missing" for that copy
