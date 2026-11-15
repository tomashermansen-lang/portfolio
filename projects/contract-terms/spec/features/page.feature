Feature: The page itself
  Rules the page keeps as a whole, checked against its source on the desk.

  @S-46 @R-13 @R-36
  Scenario: The page calls no model and sends nothing to a server
    Then index.html makes no request to a model API
    And index.html sends no data by POST, XMLHttpRequest or beacon

  @S-47 @R-43
  Scenario: The committee pages print in A4 landscape
    Then the print style for the committee pages sets the page size to A4 landscape

  @S-48 @R-51
  Scenario: The recording comes first, the live run second
    Then the play-the-run control of the checks stands before the live-run control in the page

  @S-49 @R-74
  Scenario: The wireframes are the four screens the prototype has
    Then spec/wireframes holds exactly "workbench", "step", "review" and "committee"
    And every wireframe is an SVG with a description and no figures from the data
