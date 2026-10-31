Feature: The review screen
  The analyst's desk, run under node with a stub DOM against the real files.
  Executed by tools/spec_runner.js.

  Background:
    Given the page is loaded with the recorded run

  @S-51 @R-27
  Scenario: Terms with a finding come first, then not found, then the rest
    When the contract "lichtung-offshore-ppa-execution" is open
    Then the list starts with "11_default_and_termination"
    When the contract "olivos-solar-ppa-execution" is open
    Then the list starts with "8_curtailment"

  @S-52 @R-28 @R-29
  Scenario: Selecting a term shows the answer and highlights the sentence in the contract
    When the contract "havrebakke-ppa-v2-execution" is open
    Then the detail shows the term's answer and a source sentence
    And the document pane highlights the source sentence

  @S-53 @R-30
  Scenario: A term not found highlights nothing and says so
    When the contract "olivos-solar-ppa-execution" is open
    Then the document pane says nothing is highlighted

  @S-54 @R-31 @R-32
  Scenario: Citations are links, and a missing annex is marked missing
    When the contract "lichtung-offshore-ppa-execution" is open
    And the term "11_default_and_termination" is selected
    Then the detail has a citation link marked missing for "Annex 5"

  @S-55 @R-33 @R-35 @R-42
  Scenario: Confirm and flag are recorded, counted and shown to the committee
    When the contract "havrebakke-ppa-v2-execution" is open
    And the analyst confirms the current term
    And the analyst flags the current term with a note
    Then the list shows one "confirmed" and one "flagged"
    And the status line counts 2 reviewed, 1 flagged
    And the committee page lists the flagged term under open points with the note, and marks it on its row
    And the committee page footer says 2 of 12 reviewed

  @S-56 @R-37
  Scenario: The export carries every term with its review
    When the contract "havrebakke-ppa-v2-execution" is open
    And the analyst confirms the current term
    And the analyst exports the table
    Then the CSV has a header with "review" and "review_note" and 12 term rows
    And one row says "confirmed" and the others "not reviewed"

  @S-57 @R-34
  Scenario: A flag needs a note
    When the contract "havrebakke-ppa-v2-execution" is open
    And the analyst saves a flag with an empty note
    Then no decision is recorded for the current term

  @S-58 @R-38
  Scenario: The signed version marks what changed since the draft
    When the contract "havrebakke-ppa-v2-execution" is open
    Then the list marks "5_price_and_indexation" as changed

  @S-59 @R-38a
  Scenario: Any version of the contract can be chosen from a list and read with its own sentence marked
    When the contract "havrebakke-ppa-v2-execution" is open
    And the term "5_price_and_indexation" is selected
    Then the document pane offers 2 versions in a list
    When the version "havrebakke-ppa-v1-draft" is chosen
    Then the document pane shows the draft and marks the draft's sentence for the term

  @S-60 @R-38a @pending
  Scenario: A version that does not state the term says so
    No pair of versions in the data room differs on whether a term exists; the draft
    still states curtailment by the grid operator. Needs a document pair where one
    version lacks a term the other has.
    When a version without the selected term is chosen
    Then the document pane says the version does not state the term

  @S-61 @R-65 @R-65a @R-65b @R-65c @R-65d @R-65e @R-66 @R-66a @R-67 @R-67a @R-68 @R-70 @R-70b
  Scenario: The product starts on a workbench, and its five actions run in order
    Then the prototype opens on a workbench listing every case with its status
    When the analyst starts an upload and chooses the contract "havrebakke-ppa-v2-execution"
    Then only the load action is enabled, and Next beside it is disabled
    When the analyst loads the contract
    Then step 1 shows the contract's first lines and its hash, and the analyse action is enabled
    And Next beside the action leads to step 2, where the frame speaks as the product and the note under it says the call is a recording
    And step 2 names the model and the run
    When the worked example is opened from the note under the frame
    Then step 4 is current and step 3 counts the findings for the contract, each on the list in step 4
    When the pages are built
    Then step 5 shows page 1 of the pages

  @S-62 @R-72
  Scenario: Start over clears every case
    When the analyst starts an upload and chooses the contract "havrebakke-ppa-v2-execution"
    And the analyst loads the contract
    And the worked example is opened from the note under the frame
    And the reader starts over from the note under the frame
    Then the prototype opens on a workbench listing every case with its status
