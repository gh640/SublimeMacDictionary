#!/usr/bin/python2.7
# encoding: utf-8

'''Runs the dictionary service MacOS has by default.

Usage:

echo [the word to translate] | /usr/bin/python2.7 __file__
'''


import json
import sys

from DictionaryServices import DCSGetTermRangeInString, DCSCopyTextDefinition


ENCODING = 'utf-8'
DICTIONARY = None
OFFSET = 0


def get_stdin_string_stripped():
    '''Gets the standard input string and strip it.
    '''
    return sys.stdin.read().strip()


def get_dict_definition(word_raw):
    '''Gets the definition of the specified word.
    '''
    word_range = DCSGetTermRangeInString(DICTIONARY, word_raw, OFFSET)
    try:
        word = word_raw[word_range.location:word_range.location + word_range.length]
        definition = DCSCopyTextDefinition(DICTIONARY, word_raw, word_range)
    except IndexError as e:
        raise DefinitionNotFoundException('The definition not found.')

    return word, definition


class DefinitionNotFoundException(Exception):
    '''Custom exception for the "not found" error.
    '''
    pass


if __name__ == '__main__':
    word_raw = get_stdin_string_stripped().decode(ENCODING)
    word, definition = get_dict_definition(word_raw)

    print(json.dumps({
        'word': word,
        'definition': definition,
    }))
