"""Build the deferred Rhyme Sprint index from the credited CMUdict source."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'research' / 'lexical' / 'cmudict.dict'
OVERRIDES = ROOT / 'research' / 'lexical' / 'local-pronunciations.json'
OUTPUT = ROOT / 'dist' / 'rhyme-lexicon.js'
CMUDICT_REVISION = '74790861f652b15e4ac49015a90074ad62a27690'
VOWEL = re.compile(r'^(?:AA|AE|AH|AO|AW|AY|EH|ER|EY|IH|IY|OW|OY|UH|UW)([012])$')
VARIANT = re.compile(r'\(\d+\)$')


def normalized_word(value):
    return str(value).strip().lower().replace('’', "'").replace('‘', "'")


def rhyme_part(phones):
    last_stressed_vowel = None
    for index, phone in enumerate(phones):
        match = VOWEL.fullmatch(phone)
        if match and match.group(1) in ('1', '2'):
            last_stressed_vowel = index
    if last_stressed_vowel is None:
        return None
    return ' '.join(re.sub(r'[012]$', '', phone) for phone in phones[last_stressed_vowel:])


def add_pronunciation(target, word, phones):
    word = normalized_word(word)
    if not word or not phones or not re.fullmatch(r"[^\s]+", word):
        return
    part = rhyme_part(phones)
    if part:
        target.setdefault(word, set()).add(part)


def main():
    if not SOURCE.is_file():
        raise SystemExit(f'Missing credited dictionary source: {SOURCE}')
    words = {}
    for line in SOURCE.read_text(encoding='utf-8').splitlines():
        if not line or line.startswith(';;;'):
            continue
        fields = line.split()
        if len(fields) < 2:
            continue
        add_pronunciation(words, VARIANT.sub('', fields[0]), fields[1:])

    override_data = json.loads(OVERRIDES.read_text(encoding='utf-8')) if OVERRIDES.exists() else {}
    for word, entry in override_data.get('entries', {}).items():
        if not isinstance(entry, dict) or not entry.get('source'):
            raise SystemExit(f'Local pronunciation needs a source note: {word}')
        pronunciations = entry.get('pronunciations', [])
        if not pronunciations:
            raise SystemExit(f'Local pronunciation needs at least one pronunciation: {word}')
        for pronunciation in pronunciations:
            phones = str(pronunciation).upper().split()
            if not all(re.fullmatch(r'[A-Z]+[012]?', phone) for phone in phones):
                raise SystemExit(f'Invalid ARPAbet phones for {word}: {pronunciation}')
            add_pronunciation(words, word, phones)

    payload = {
        'source': f'CMUdict {CMUDICT_REVISION}',
        'wordRimes': {word: sorted(rimes) for word, rimes in sorted(words.items())},
    }
    OUTPUT.write_text(
        '(function(root){root.PoeticsRhymeLexicon=' + json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + ';})(typeof window!=="undefined"?window:globalThis);\n',
        encoding='utf-8', newline='\n',
    )
    print(f'Built {len(words):,} words from CMUdict {CMUDICT_REVISION}')


if __name__ == '__main__':
    main()
