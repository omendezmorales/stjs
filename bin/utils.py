'''Utilities used across all tools.'''


import argparse
import re
import sys
import yaml


# Width of output lines.
WIDTH = 72

# Length of included chunks.
LENGTH = 30

# Glossary references use <span g="...">...</span>.
GLOSS_REF = re.compile(r'<span\s+g="(.+?)">', re.DOTALL)

# Patterns to remove from input when tokenizing Markdown source files.
ALWAYS = [
    re.compile(r'---'),                                         # em-dashes
    re.compile(r'[©×μ…]'),                                      # strange characters
    re.compile(r'```.+?```', re.DOTALL),                        # code blocks
    re.compile(r'`.+?`', re.DOTALL),                            # inline code
    re.compile(r'{%\s+raw\s+%}.*?{%\s+endraw\s+%}', re.DOTALL), # raw blocks
    re.compile(r'<div\s+class="callout"\s*markdown="1">'),      # opening callout
    re.compile(r'</div>')                                       # closing callout
]
SCRUB = [
    re.compile(r'{%\s+include\s+.+?%}', re.DOTALL),             # inclusions
    re.compile(r'{:\s+.continue\s*}', re.DOTALL)                # continued paragraphs
]
REPLACE = [
    re.compile(r'\[(.+?)\]\[.+?\]', re.DOTALL),                 # link reference (keep text)
    re.compile(r'\[(.+?)\]\(.+?\)', re.DOTALL)                  # link reference (keep text)
]
SPANS = [
    re.compile(r'<span\b.+?>', re.DOTALL),                      # opening <span>
    re.compile(r'</span>', re.DOTALL),                          # closing <span>
    re.compile(r'<cite>.+?</cite>', re.DOTALL)                  # citations
]

def get_all_matches(pattern, filenames, group=1, scrub=True, no_duplicates=False):
    '''Create set of matches in source files.'''
    result = set()
    for filename in filenames:
        duplicates = []
        result |= get_matches(pattern, filename, group, scrub, duplicates)
        if duplicates and no_duplicates:
            print(f'** duplicate key(s) {duplicates} **', file=sys.stderr)
    return result


def get_entry_info(config):
    '''Return dictionary of {slug, filename, label} for all chapters.'''
    num_chapters = None
    kind = 'Chapter'
    result = []
    for (i, entry) in enumerate(config['chapters']):
        if 'appendix' in entry:
            num_chapters = i + 1
            kind = 'Appendix'
            continue
        title = entry['title']
        slug = entry['slug']
        filename = entry['file'] if ('file' in entry) else f'./{entry["slug"]}/index.md'
        label = f'{i+1}' if (num_chapters is None) else chr(ord('A') + i - num_chapters)
        result.append({'slug': slug,
                       'title': title,
                       'file': filename,
                       'kind': kind,
                       'label': label})
    return result


def get_matches(pattern, filename, group=1, scrub=True, duplicates=None):
    '''Get matches from a single file.'''
    result = set()
    text = read_file(filename, scrub)
    for match in pattern.finditer(text):
        for key in match.group(group).split(','):
            if (duplicates is not None) and (key in result):
                duplicates.append(key)
            result.add(key.strip())
    return result


def get_options(*options):
    '''Get command-line options.'''
    parser = argparse.ArgumentParser()
    for [flag, nargs, explain] in options:
        if nargs is None:
            parser.add_argument(flag, action='store_true', help=explain)
        elif nargs:
            parser.add_argument(flag, nargs='+', help=explain)
        else:
            parser.add_argument(flag, help=explain)
    return parser.parse_args()


def get_words(filename):
    '''Get words from a file for spell-checking.'''
    from nltk.tokenize import TweetTokenizer # loaded here to cut run time
    text = read_file(filename, scrub=True)
    for pattern in SPANS:
        text = pattern.sub(' ', text)
    for pattern in REPLACE:
        text = pattern.sub(lambda x: x.group(1), text)
    tokenizer = TweetTokenizer()
    return set(tokenizer.tokenize(text))


def read_file(filename, scrub=True):
    '''Read a file, removing raw sections if requested.'''
    with open(filename, 'r') as reader:
        text = reader.read()
        for pattern in ALWAYS:
            text = pattern.sub(' ', text)
        if scrub:
            for pattern in SCRUB:
                text = pattern.sub(' ', text)
        return text


def read_yaml(filename):
    '''Load and return a YAML file.'''
    with open(filename, 'r') as reader:
        return yaml.load(reader, Loader=yaml.FullLoader)


def report(title, checkOnlyRight=True, **kwargs):
    '''Report items if present.'''
    assert len(kwargs) == 2, 'Must have two sets to report'
    left, right = kwargs.keys()
    onlyLeft = kwargs[left] - kwargs[right]
    onlyRight = kwargs[right] - kwargs[left]
    if onlyLeft or (checkOnlyRight and onlyRight):
        print(f'- {title}')
        if onlyLeft:
            print(f'  - {left} but not {right}')
            for item in sorted(onlyLeft):
                print(f'    - {item}')
        if checkOnlyRight and onlyRight:
            print(f'  - {right} but not {left}')
            for item in sorted(onlyRight):
                print(f'    - {item}')


def write_yaml(filename, data):
    '''Save a YAML file.'''
    with open(filename, 'w') as writer:
        return yaml.dump(data, writer)
