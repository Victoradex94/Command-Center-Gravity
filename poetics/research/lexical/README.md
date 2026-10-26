# Rhyme Sprint pronunciation data

`cmudict.dict` is the CMU Pronouncing Dictionary source at commit
`74790861f652b15e4ac49015a90074ad62a27690`. Its upstream README identifies it
as the Carnegie Mellon University pronouncing dictionary, permits research and
commercial use, and requests attribution. The matching upstream license is
retained in `CMUDICT-LICENSE`.

`scripts/build-rhyme-lexicon.py` builds `dist/rhyme-lexicon.js` from that pinned
source. The generated index stores each recognized word's rime from its last
primary or secondary stressed vowel. The file is fingerprinted as a separate
lazy asset and is requested only when the player opens Rhyme Sprint.

The CMU source reflects North American English pronunciation and is not a
complete word list or a Nigerian English pronunciation authority. Add a local
entry to `local-pronunciations.json` only after its pronunciation is reviewed;
record a source note and provide one or more CMU-style ARPAbet pronunciations.
The builder merges those entries with CMUdict. Existing hand-curated near-rhyme
exceptions remain explicit in `dist/rhyme-game.js`.
