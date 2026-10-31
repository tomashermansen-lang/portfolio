Feature: Scoring against the answer key
  Every run is scored term by term against spec/answer-key.json.

  @S-10 @R-14 @R-15
  Scenario: A term is right when its figures are present and its quote is verbatim
    Given a key term present with facts "12" and quote "Supply Period: twelve (12) years commencing on the Commercial Operation Date."
    When the model answers found with value "The Supply Period is twelve years from COD" and that quote
    Then the verdict is "correct"

  @S-11 @R-15
  Scenario: Number words count as figures
    Given a key term present with facts "12" and quote "Supply Period: twelve (12) years commencing on the Commercial Operation Date."
    When the model answers found with value "ten years from COD" and that quote
    Then the verdict is "wrong_value"

  @S-12 @R-16
  Scenario: An absent term is right only when reported not found
    Given a key term absent
    When the model answers not found
    Then the verdict is "correct"
    When the model answers found with value "Buyer may curtail 100 hours" and quote "x"
    Then the verdict is "invented"

  @S-13 @R-17
  Scenario: A verbatim quote from another sentence is right, and flagged
    Given a key term present with facts "12" and quote "Supply Period: twelve (12) years commencing on the Commercial Operation Date."
    When the model answers found with value "12 years" and quote "Longstop Date means 31 March 2028."
    Then the verdict is "correct"
    And the source is recorded as not matching the key

  @S-14 @R-14 @R-18
  Scenario: The recorded runs score the same and the misses are named
    Given the recorded runs
    Then run 1 scores 46 correct of 48
    And the term "12_change_in_law_and_force_majeure" of "lichtung-offshore-ppa-execution" is correct in 0 of 5 runs
    And the term "7_product_and_certificates" of "lichtung-offshore-ppa-execution" is correct in 1 of 5 runs

  @S-15 @R-19
  Scenario: A committee paper is read as written, errors included
    Given the recorded runs
    Then the paper "havrebakke-ic-key-terms" is faithful on "3_supply_period" and "10_credit_support"

  @S-16 @R-81 @R-64
  Scenario: Every run's score is available to the business case
    Given the recorded runs
    Then every recorded run has a score of correct terms out of 48
    And the lowest and highest run scores are 46 and 47
