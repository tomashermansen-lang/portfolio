Feature: The handover and what the page runs
  The stories table, the code shown as it is, and the replay that says it is one.
  Executed by tools/spec_runner.js.

  Background:
    Given the page is loaded with the recorded run

  @S-69 @R-73 @R-73a @R-73c
  Scenario: Every story links to a requirement and to a scenario that exist
    Then the stories table lists at least 8 stories in at least 5 epics
    And every requirement link of a story points at a rendered requirement
    And every acceptance link of a story points at a rendered scenario
    And every story shows a prototype status of "Shown", "Partly" or "Not built"

  @S-73 @R-73b
  Scenario: The phase filter narrows the table to the stories of one phase
    When the phase filter is set to "pilot"
    Then every listed story is in phase "Pilot" and the count line says how many of the total are listed

  @S-75 @R-73b
  Scenario: Sorting by priority lists every Must story before any Should or Could
    When the sort is set to "priority"
    Then no story of priority "Should" or "Could" is listed before one of priority "Must"

  @S-74 @R-73d @R-73c
  Scenario: The discovery is closed by its deliverables, and the backlog holds only the phases that follow
    Then the discovery block above the stories lists 6 deliverables
    And every story is in phase "Pilot" or "Build"
    And every story carries a requirement or says where it will be written
    And no requirement of the product is outside a story

  @S-70 @R-50
  Scenario: The code that runs is shown as it is on disk
    Then the checks file is shown with its line count

  @S-77 @R-50a
  Scenario: The scorer is shown as it is on disk in the eval fold, with its recorded run
    Then the scorer file is shown with its line count in the eval fold
    And the recording has a section for the scorer, and its play control sits in the eval fold

  @S-71 @R-52
  Scenario: A replay says on its first line that it is a recording
    When the recording of the checks is played
    Then the first line of the console says it is a recording and that nothing ran in the browser

  @S-72 @R-83 @R-84 @R-84a @R-85 @R-86 @R-87 @R-88 @R-89 @R-90 @pending
  Scenario: The technical requirements name what is decided and what the architect decides
    Pending: the deployment, integration, database, cost ceiling and queueing are decided by the solution architect at the pilot; the page lists each with its constraint.
    Then every technical requirement states whether it is decided or open, and an open one names the constraint it must respect

