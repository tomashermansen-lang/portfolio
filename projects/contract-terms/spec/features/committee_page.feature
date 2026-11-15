Feature: The committee page
  Four landscape pages built from the reviewed table, and the business case that
  reports on them. Executed by tools/spec_runner.js.

  Background:
    Given the page is loaded with the recorded run

  @S-63 @R-39 @R-39a @R-39b @R-39c
  Scenario: A summary first, the twelve terms in full over as many pages as they need, open points last
    Then the deck has 5 pages
    And page 1 has "In brief" and refers to the term pages and the last page
    And the term pages list terms 1 to 12 in order, at most four per page, each with its full answer and a clause
    And the last page has "Open points" and "Changed since the draft"

  @S-64 @R-40 @R-40a @R-39b
  Scenario: A citation that does not exist is an open point
    When the contract "lichtung-offshore-ppa-execution" is open
    And the pages are built for the open case
    Then the last page lists an open point on "Events of default, termination and termination amount"
    And the last page lists no paper disagreement

  @S-65 @R-41
  Scenario: Every page states its provenance
    Then every page names the model, the run and the date

  @S-66 @R-49a @R-49b @R-49c @R-49d @R-77 @R-81
  Scenario: Version 2 of the business case asks the board for the next decision
    Then version 2 has the sections of version 1, the decision asked, a decision rule with three criteria and their dry-run status, promised against measured, and risks with a status
    And the dry run is stated in the head and the foot, not in the recommendation
    And version 2 reports the terms confirmed as read from the review log and the terms read right from the evaluation

  @S-84 @R-92
  Scenario: Pages of a version with unreviewed terms are a draft, and can be printed only when every term is reviewed
    Then every page carries the mark DRAFT and the print control is disabled
    And page 1 says first how many terms are not yet reviewed
    When every term of the open case is confirmed
    Then no page carries the mark DRAFT and the print control is enabled

  @S-82 @R-43a @pending
  Scenario: The reviewed figures leave the product for the financial model without retyping
    Given a contract whose twelve terms are all reviewed
    Then an export holds one row per term with the figure, its unit and the reference of its sentence, in the format the financial model takes

  @S-67 @R-69 @R-69a
  Scenario: The handover holds the package with its evidence, the reasoning sits behind the case
    Then the handover, with every fold closed, comes before the chapter behind the case
    And the key, the scored runs and the scorer sit in the eval fold of the handover
