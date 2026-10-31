Feature: Deterministic checks
  What code can check is checked by code, on the recorded run, with the
  standard library only.

  Background:
    Given the recorded run 1
    And the documents of the data room

  @S-17 @R-20 @R-90
  Scenario: The checks need nothing but the standard library
    Then tools/checks.py imports only "difflib", "json" and "re"

  @S-18 @R-21
  Scenario: Every quote of run 1 is in its document
    Then the verbatim check raises no finding on any contract

  @S-19 @R-21
  Scenario: A paraphrased quote is a finding
    When the quote of "3_supply_period" in "havrebakke-ppa-v2-execution" is replaced by "Supply Period: twelve years commencing on COD."
    Then the verbatim check raises a finding on "3_supply_period"

  @S-20 @R-22
  Scenario: Citations must point at clauses that exist
    Then the citation check on "olivos-solar-ppa-execution" raises no finding
    And the citation check on "lichtung-offshore-ppa-execution" raises exactly one finding, on "11_default_and_termination", citing "Annex 5"

  @S-21 @R-23
  Scenario: The committee paper disagrees with the contract on two figures and nothing else
    When "havrebakke-ic-key-terms" is checked against "havrebakke-ppa-v2-execution"
    Then the findings are exactly "3_supply_period" years and "10_credit_support" eur
    And the finding on "3_supply_period" says the paper states 10 and the contract 12

  @S-22 @R-23
  Scenario: The legal summary disagrees on one figure
    When "havrebakke-legal-dd-summary" is checked against "havrebakke-ppa-v2-execution"
    Then the findings are exactly "3_supply_period" years

  @S-23 @R-24
  Scenario: The draft and the signed version differ on the negotiated terms
    When "havrebakke-ppa-v1-draft" is compared with "havrebakke-ppa-v2-execution"
    Then the changed terms include "3_supply_period", "4_cod_and_delay", "5_price_and_indexation", "8_curtailment" and "10_credit_support"
    And "2_facility" and "7_product_and_certificates" are unchanged

  @S-80 @R-24
  Scenario: A figure the model's wording dropped is not a change when the contract still states it
    The draft's extraction mentions 75 per cent of P50, the final's does not; both contracts state the 75 per cent.
    When "havrebakke-ppa-v1-draft" is compared with "havrebakke-ppa-v2-execution"
    Then "6_volume_and_performance" is unchanged, because both versions state its figures

  @S-24 @R-25
  Scenario: The document diff shows the negotiated changes without a model
    When the texts of "havrebakke-ppa-v1-draft" and "havrebakke-ppa-v2-execution" are diffed
    Then the draft side contains "ten (10) years" and "EUR 58.00"
    And the signed side contains "twelve (12) years" and "EUR 54.50"

  @S-25 @R-26
  Scenario: A malformed record is a shape finding
    When a record marks "3_supply_period" found without a quote
    Then the shape check raises a finding on "3_supply_period"
