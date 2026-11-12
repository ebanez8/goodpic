# Experiment history

The supplied brief reports a prior `t/output/experiment.py` that injected strokes into `.goodnotes` archives. On manual Goodnotes import, objects appeared, were movable and deletable, and persisted after reopening. Their appearance was distorted; partial stroke erasing was not conclusively tested. These are user-reported observations, pending access to the original experiment.

Filesystem inspection on 2026-10-21 found no `t/` directory or `t/test.goodnotes` in this checkout. The workspace root is a `goodparse` repository with `samples/`, `src/goodparse/`, and its own packaging. No existing files were moved or altered. When `t/` becomes available, inspect it read-only and append exact file hashes, commands, and findings here.

## 2026-10-30 local experiments

`t/` is still absent, so the historical script could not be adapted directly. The available `samples/test.goodnotes` was used as the document template and `samples/Test4.goodnotes` as the genuine vA pen source. `generated/phase2_experiments/` contains six independent outputs: `genuine_clone`, `translated`, `scaled`, `straight`, `letter_a`, and `inksight_word`. Each `diagnostic.json` lists modified fields. The word fixture is a real seven-stroke InkSight run on Google's official `word.jpg` (95.48 seconds in WSL). The clone keeps raw geometry identical; translation and uniform scale transform sampled, outline, and control geometry; the three generated cases warp all those representations to target strokes. Every archive passed ZIP integrity and independent goodparse parsing, with one native record per input stroke. No actual Goodnotes rendering was available, so visual fidelity and partial erasing remain unverified.

## User Goodnotes import feedback, 2026-10-30

The user imported the first set and supplied screenshots. The unchanged genuine loop appeared as a red O, and a long curved line appeared in the page center. The generated straight/A/word paths did not visibly match their reference previews and appeared absent in the supplied views. The central curve is an existing object in `samples/test.goodnotes`; the original encoder appended to that page. The red O is the cloned Test4 loop. The earlier claim of only structural validation remains valid, but visual compatibility is now **observed to fail** for that set. Revision v2 clears the target page and uses a near-straight Test5 pen source for generated paths. V2 still needs a Goodnotes import to judge whether its path reconstruction works.
