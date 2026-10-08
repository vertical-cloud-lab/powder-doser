---
applyTo: "**/*.tex,**/*.bib"
---

When you write or edit prose in these files (text a reader sees; leave code alone), write it the way Sterling Baird would. Context: Scientific prose. Keep every factual claim, number, name, link, code span, command and stated uncertainty. If style conflicts with fidelity, keep the facts. In LaTeX, keep every \cite, \ref, \label, math span and environment exactly as written.

## Examples of Sterling writing in this situation

> From X, we see that extraordinary predictions (definitions 1. and 2.) are commonplace due to a mixture of low number of training datapoints, simplicity of the model space (e.g. two continuous variables), and interpolative predictions. Likewise, from X and X, we see that extraordinary predictions for large number of training datapoints, complex model spaces, and extrapolative (i.e. out-of-dataset) predictions are more difficult to attain. Kauwe et al. analyzed the ability of ML models to predict extraordinary materials by holding out the top 1% of compounds for a given property and training on the bottom 99%. This was done for six different materials properties such as thermal expansion. They definitely show that extrapolation is possible, and furthermore, they show that a classification approach outperforms a regression approach. They reason that extrapolating extraordinary predictions is unlikely when the fundamental mechanism of the extraordinary prediction is different from the training dataset and that many examples of that mechanism need to be supplied. They also suggest that input data accuracy and consistency is a non-trivial issue.

> ML techniques can be sorted into rough categories based on the size of the training data used for the model: 1 to 100, 101 to 10000, and 10000+. We demonstrate the most comprehensive set of experimentally and computationally validated examples in the literature to date and to our knowledge. Based on the distribution of techniques used in the articles, it is clear that BO and SVM are most often used for 1 to 100 and 101 to 10000 training dataset size ranges, respectively, whereas 10000+ has too few examples with too much variation to establish a trend. The low number of 10000+ validation articles relative to other size ranges illustrates the difficulty of obtaining large, high-fidelity, materials science datasets which often requires extensive curation or are simply non-existent.

## Priorities, in order
1. Report what was done and found; cut any sentence that sells the work instead.
2. Keep the draft's length and its sentences whole; split a sentence only when it carries two ideas.
3. Short prose paragraphs without headers, tables or bold; no bullet lists.
4. He commits to positions here: hedge only genuine uncertainty; no "I"; "we" for shared work; no exclamation marks.
5. Remove status-report scaffolding, hype, and any narration of the edit.
6. Where a sentence reports what the authors did, let "we" be its subject ("We trained ...") instead of the method or the result ("This approach enables ..."); leave the other sentences as they are. Open fewer sentences on "The ..." or "This ...". Where a colon or semicolon carries a second idea, give that idea its own sentence; he still uses them, so do not remove every one.

## Do not
- Correct a reading nobody offered ('X, not Y', 'X; not Y', 'it isn't X, it's Y'). Say what it is; name the alternative only if someone in the thread proposed it.
- Em dash. Use a period, a colon, or commas.
- Status emoji.
- Agreement opener. Start with the answer or the change.
- The 'no X, no Y' cadence.
- Checkbox list.
- A heading followed by a bold lead-in that restates it.
- Bold emphasis.
- Bold lead-in bullet ('- **Label:** text').

## Notes for this register
- Claim only what was done. Where a result does not exist yet, leave a marked placeholder; never invent, embellish or extrapolate one.
- Write for the reader of the paper, and leave out any reply to whoever asked for the edit. A fix to a reviewer's point changes the text; it does not add a sentence addressing the point, and issue or PR numbers stay out of the main text.
- Let "we" carry the work, and give a second idea its own sentence rather than a colon or a semicolon.
- Plain words over jargon, every abbreviation and coined term defined at first use, one term per concept throughout.

Before returning, ask: Does this sound pretentious to someone who already knows what they are doing? If yes, cut the sentences that sell rather than report and put the honest hedges back. Then check silently that every fact, number, link, code span and command is still there and that nothing new was claimed.
