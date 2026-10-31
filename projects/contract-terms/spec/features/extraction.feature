Feature: Extraction records
  The model run is recorded, one JSON record per document per run, and every
  record has the shape the rest of the method depends on.

  Background:
    Given the recorded run 1

  @S-01 @R-01 @R-02
  Scenario: Twelve terms, defined once
    Then spec/terms.json defines exactly 12 terms, each with an id, a label and a definition
    And every record of run 1 holds those 12 terms in that order

  @S-02 @R-07 @R-26
  Scenario: A found term carries its evidence
    Then every term reported found has a value, a quote and a clause

  @S-03 @R-08
  Scenario: A silent contract is left blank
    When the term "8_curtailment" of "olivos-solar-ppa-execution" is read
    Then the term is not found
    And the note says the document does not address it

  @S-04 @R-09
  Scenario: A term defined by reference to a missing annex is not found
    When the term "11_default_and_termination" of "lichtung-offshore-ppa-execution" is read
    Then the term is not found
    And the note mentions "Annex 5"

  @S-05 @R-06
  Scenario: The price is read from the annex the body refers to
    When the term "5_price_and_indexation" of "havrebakke-ppa-v2-execution" is read
    Then the value contains "54.50"
    And the clause mentions "Annex 2"

  @S-06 @R-10 @R-11
  Scenario: Every record says which model, when, and on which text
    Then every record of run 1 carries a model, a run time, a run number and a 64-character document hash
    And the document hash of "havrebakke-ppa-v2-execution" matches the SHA-256 of dataroom/havrebakke-ppa-v2-execution.md
    And the runs are numbered 1 to 5 with no gap

  @S-07 @R-12
  Scenario: The raw reply is kept beside the parsed record
    Then the extractor writes the raw model reply to a file beside the record before it parses it
