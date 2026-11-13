Feature: Intake, platform and lifecycle
  What a solution architect asks first, specified after the external review of
  2026-10-31. Every scenario here is pending: specified for the pilot or the build,
  with nothing on this page to run it against. Reported as pending, never as passed.

  @S-83 @R-91 @pending
  Scenario: A real contract enters as PDF or DOCX, with its pages kept and its gaps named
    Given a contract as a PDF with an annex named in the body but not attached
    Then the text is extracted with the page number of every sentence, and the load is rejected naming the missing annex

  @S-85 @R-93 @pending
  Scenario: No more than the contract text and the twelve definitions leave for the model
    Given a contract read through the approved path
    Then the call record shows the contract text and the definitions and nothing else was sent

  @S-86 @R-95 @pending
  Scenario: A failed or unreadable model call is retried once and then shown on the case
    Given a model call that fails twice for one document of six
    Then the document is marked "not read" on the case with the reason, and the other five have their records

  @S-87 @R-96 @pending
  Scenario: A re-read becomes the current run for that version, and earlier runs stay on file
    Given a document read twice on the same version
    Then the case shows the later run as current and keeps the earlier one, never shown as current

  @S-89 @R-97 @pending
  Scenario: An instruction planted inside a contract is read as contract text
    Given a data-room document with an instruction to the model inside an annex
    Then the extraction ignores the instruction, and the eval scores that document like any other

  @S-90 @R-98 @R-84a @pending
  Scenario: A person without access to the deal does not see the case
    Given a person with no access to the deal in the document system
    Then the case, its extractions and its review log are not listed for that person

  @S-91 @R-99 @pending
  Scenario: Every read of a review log or an export is logged for the audit function
    Given a review log opened and a table exported
    Then the access log holds who and when for both, readable without the application

  @S-92 @R-100 @pending
  Scenario: When the document system or the model is down, the case says which step cannot run
    Given the model unavailable
    Then the case shows the analyse step as unavailable with the reason, and the last reviewed table still opens

  @S-93 @R-101 @pending
  Scenario: A change of definitions or prompt marks earlier extractions stale until re-read
    Given a prompt template with a new version
    Then every extraction made with the earlier version is marked stale on its case, and pinning the previous version clears the mark

  @S-94 @R-102 @R-87 @pending
  Scenario: At the cost ceiling the model is not called and the analyst is told
    Given the monthly cost ceiling reached
    Then no model call is made, the case says the contract waits for the next month or a raised ceiling, and the product manager is notified

  @S-95 @R-103 @pending
  Scenario: An error rate above the threshold puts a warning on the committee pages
    Given a monthly error rate above the threshold set in the business case
    Then every committee page carries the warning, and the owner's decision on the method is recorded

  @S-96 @R-104 @pending
  Scenario: A regression from correct blocks a release until its reason is written
    Given a new prompt version scored against the key with one term regressed from correct
    Then the release is blocked until the product manager writes the reason in the release record

  @S-97 @R-105 @pending
  Scenario: The handover names the scenarios that carry over and the ones rewritten
    Then the file-level scenarios are listed as the build's regression suite unchanged, and the screen scenarios as rewritten against the house's test runner

  @S-98 @R-106 @pending
  Scenario: Decisions on an earlier version are kept, and a case can leave as one file
    Given a new version of a contract loaded over a reviewed one
    Then the earlier decisions are shown as made on that version, and the case exports as one JSON file with hashes, extractions, checks and review log

  @S-99 @R-84 @pending
  Scenario: A contract in the pipeline appears in its case without a copy leaving the document store
    Given a contract filed in the document system under its deal
    Then its case lists the contract read through the document system's own access control, and no copy is made outside it

  @S-100 @R-83 @pending
  Scenario: A document goes only to the approved model deployment
    Given the model deployment whose terms security and legal have settled
    Then every call record names that deployment, and no call goes anywhere else

  @S-101 @R-88 @pending
  Scenario: A 130-page contract is read within ten minutes, or the analyst is told
    Given a contract of 130 pages uploaded
    Then the read table is on the case within ten minutes, or the case says it is taking longer

  @S-102 @R-85 @R-89 @pending
  Scenario: A decision outlives the browser tab and the audit trail names who, when and on which version
    Given a term confirmed on the review screen
    Then the decision is in the firm's database after the tab is closed, with the reviewer, the time and the document hash

  @S-103 @R-86 @pending
  Scenario: Every record carries the model version and the prompt version
    Given an extraction record
    Then it names the model version and the prompt version it was made with
