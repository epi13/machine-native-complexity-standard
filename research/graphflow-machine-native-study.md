# Preliminary GraphFlow machine-native study

## Scope

The motivating experiment covered one bounded task: an incremental HTTP chunked
transfer decoder in portable C11. It compared an ordinary machine-native control
with an agent-visible compact Joern condition across five paired repetitions. This
is preliminary motivation, not normative evidence for MNCS and not evidence of
generality beyond the tested task, prompt, model, effort, evaluator, or host.

All ten final candidates passed primary and holdout evaluation. Both machine-native
conditions outperformed the readable reference on average: the control geometric
mean speed ratio was 1.1657 and the compact-structural condition's was 1.1379. The
ordinary control therefore outperformed the agent-visible compact Joern condition
on average. The treatment/control paired geometric mean was 0.9761, with one
treatment win, three control wins, and one tie under the declared ±2% noise band.

The five pairs are exploratory and do not establish statistical significance. A
descriptive bootstrap interval crossed parity, and the experiment did not resolve
order effects: the two compact-first pairs both favored control, while the three
control-first pairs had one treatment win, one control win, and one tie. These
patterns are not causal findings.

## What was and was not measured

Correctness, holdout correctness, performance, structural complexity, token cost,
elapsed time, and checker use were recorded separately. Correlation between a
complexity delta and speed is descriptive, not causal. Input tokens and cached input
tokens were separate fields. Median elapsed time and input token use were higher in
the compact-structural condition. Checker ledgers showed bounded invocations, but
persistent agent-visible Joern feedback was not shown to improve optimization.

Tool-neutral structural verification may still be useful as an external rejection
gate or as compact, exception-driven repair feedback when it finds a concrete
violation that runtime evaluation missed. That engineering hypothesis is distinct
from optimization guidance.

Joern is optional and is not a normative MNCS dependency. The experiment does not
show that Joern caused any optimization, proves C semantics, or improves outcomes in
other tasks.

## Compact source evidence

Evidence was inspected from the GraphFlow research tree without copying raw
transcripts or large result files. SHA-256 identities:

- fixed task: `38f81f4aaa804847579cdd3433d36b7b420cf08fde519748bd2683195aae9b15`
- aggregate Markdown:
  `df7b55fa98da5f1372af6ccf5e1359521ba2f4d8efe563537f0a76a98665e7c0`
- aggregate JSON:
  `b5eb120f93f54357d0d054e03741bb7094686255b9e0552f4b483832eb1066e5`
- task manifest:
  `e31d8c289e324660fe625a85aa877a5c5ef1ecf5eced22ea63549d46e8f251f4`

These hashes identify evaluator-owned source evidence as inspected for this note;
they do not make the external research repository part of an MNCS bundle.
