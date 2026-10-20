import os

work = r'C:\Users\Victor Adetimilehin\Documents\Codex\2026-10-19\update-the-private-github-repository-victoradex94\work\poetics-staging-connector\poetics'
os.chdir(work)

with open('dist/opportunities.4ddfcc6ef954.js', 'r', encoding='utf-8') as f:
    opp_orig = f.read()

with open('dist/rhyme-game.js', 'r', encoding='utf-8') as f:
    rhyme = f.read()

# Replace the module.exports in rhyme so that it augments module.exports instead of replacing it
rhyme_mod = rhyme.replace(
    "if (typeof module !== 'undefined') module.exports = api;",
    "if (typeof module !== 'undefined') { Object.assign(module.exports, api); }"
)

combined = opp_orig.rstrip() + "\n\n" + rhyme_mod.lstrip()

with open('dist/opportunities.js', 'w', encoding='utf-8') as f:
    f.write(combined)

print("Successfully merged dist/opportunities.js")
