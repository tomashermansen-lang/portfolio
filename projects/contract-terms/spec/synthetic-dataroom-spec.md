# Synthetic data room — specification

Purpose: a small, fictional data room for one investment case, used to show a
method: extract the key terms of a power purchase agreement (PPA) into the
table an investment committee reads, with the source line beside each term,
a blank where the document is silent, and a flag where the committee paper
disagrees with the contract.

Everything here is fictional. Parties, places (except countries and bidding
zones), numbers and dates are invented. Each document carries the header line:

> Synthetic document, written to demonstrate a method. Fictional parties and
> figures. Not a real contract and not legal advice.

## Structure of every PPA (after the EFET / RE-Source template, 2019)

Source for the structure: Energy Traders Europe (EFET) presentation on the
standard PPA, 2026 (data/public/efet-intro-2026.txt), and the executed public
PPAs in data/public/. The text is written from scratch; no sentence is copied
from any real contract.

- Cover page: title, parties, date, execution version marker, the synthetic
  header line.
- Table of contents.
- **Part I — Individual Terms** (the commercial elections): Parties; Facility;
  Supply Period; Product and Certificates; Contract Quantity / volume
  structure; Price (reference to the Election Sheet where the spec says so);
  Settlement (physical or financial); Delivery Point and Balancing; Credit
  Support; Governing law election; list of Annexes.
- **Part II — General Provisions**, numbered sections: 1 Definitions and
  Interpretation; 2 Conditions Precedent; 3 Construction, Milestones and
  Commercial Operation; 4 Delivery and Acceptance (or Settlement, for the
  financial PPA); 5 Forecasting, Scheduling and Outages; 6 Metering;
  7 Price, Invoicing and Payment; 8 Guarantees of Origin; 9 Credit Support;
  10 Force Majeure; 11 Change in Law (ONLY where the answer key says it is a
  defined term); 12 Events of Default; 13 Termination and Termination Amount;
  14 Limitation of Liability; 15 Insurance; 16 Assignment and Lender
  Protections; 17 Taxes, Levies and Regulatory Costs; 18 Confidentiality;
  19 Notices; 20 Governing Law and Dispute Resolution; 21 Miscellaneous.
- Annexes: Annex 1 Facility description; Annex 2 Election Sheet (price and
  commercial elections) where the spec puts the price there; Annex 3 Form of
  Letter of Credit / Guarantee; Annex 4 Parent Company Guarantee (where
  applicable); Annex 5 as the spec says.

Length per contract: 5,000–6,500 words (12–15 pages when rendered).
Register: plain, modern European contract English, numbered clauses,
defined terms capitalised and defined in section 1. Realistic but readable;
no archaic "hereinafter" chains. Dates written as "1 October 2027".

## Hard rules for the writers

1. Every quote in spec/answer-key.json for your document must appear
   **verbatim** (character for character, same capitalisation and
   punctuation) somewhere in your document. The validator greps for them.
2. Every term the answer key marks `"present": false` must be genuinely
   absent: the listed `forbidden_words` must not appear anywhere in the
   document, in any case or inflection.
3. No real company, law firm, bank or rating agency names. Use the fictional
   names in the answer key. Countries, bidding zones (DK1, ES, DE-LU),
   exchanges by generic name ("the day-ahead market") are fine.
4. Nothing copied from the public contracts in data/public/. They are for
   structure and register only.
5. The document is self-consistent: a number that appears twice is the same
   number both times, unless the answer key says the document contains a
   planted inconsistency (none of the three contracts do; the inconsistencies
   live in the DD summary and the IC table).
6. Write the whole document in one file, Markdown, headings with `#`/`##`/
   `###`, clause numbers as text ("7.3"), the synthetic header line directly
   under the title.

## The documents

| File | What | Trap it carries |
|---|---|---|
| havrebakke-ppa-v2-execution.md | Danish onshore wind, 48 MW, pay-as-produced, physical, industrial buyer with parent guarantee. Execution version 28 May 2026. | Price is NOT in the body; the body says it is in Annex 2 (Election Sheet), and Annex 2 holds it. |
| havrebakke-ppa-v1-draft.md | The same contract as the draft of 12 March 2026, before the last negotiation round. | Differs from v2 in exactly the items listed in the answer key (term, price, indexation, buyer LC, curtailment right, longstop). Everything else identical. |
| olivos-solar-ppa-execution.md | Spanish solar PV, 90 MWp / 75 MW AC, pay-as-produced, physical, buyer is an energy trader. Execution version 14 February 2026. | Curtailment is never mentioned. Change in law is not a defined term; the allocation hides in section 17 (Taxes, Levies and Regulatory Costs). |
| lichtung-offshore-ppa-execution.md | German offshore wind, 300 MW, baseload volume, financial settlement against the day-ahead price, chemical-industry buyer. Execution version 3 November 2025. | Termination Amount is defined only by reference to Annex 5, and the list of annexes says Annex 5 is "to be agreed prior to Financial Close" and it is not attached. |
| havrebakke-legal-dd-summary.md | Two-page legal due diligence summary of Havrebakke v2 by a fictional law firm. | States the Supply Period as ten years (the v1 figure). Everything else correct. |
| havrebakke-ic-key-terms.md | The key-terms table from the investment committee paper for Havrebakke. | Carries the ten-year error from the DD summary, and mis-states the Seller's performance security as EUR 2,500,000. |

## The twelve terms (the columns of the committee table)

1. Parties and buyer credit standing
2. Facility: technology, capacity, location
3. Supply period (delivery term) and its start
4. Commercial operation date, longstop and delay damages
5. Contract price and indexation
6. Volume structure, expected production and performance guarantee
7. Product and certificates (guarantees of origin, capacity)
8. Curtailment: who may curtail, cap, deemed delivery
9. Delivery point, settlement type and balancing responsibility
10. Credit support from each party
11. Events of default, termination and termination amount
12. Change in law and force majeure allocation
