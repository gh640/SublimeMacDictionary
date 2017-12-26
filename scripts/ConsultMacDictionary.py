#!/usr/bin/python2.7
# encoding: utf-8

'''Runs the dictionary service MacOS has by default.

Usage:

echo [the word to translate] | /usr/bin/python2.7 __file__
'''


import sys

from DictionaryServices import DCSGetTermRangeInString, DCSCopyTextDefinition


ENCODING = 'utf-8'
DICTIONARY = None
OFFSET = 0


def get_stdin_string_stripped():
    '''Gets the standard input string and strip it.
    '''
    return sys.stdin.read().strip()


def get_dict_definition(word):
    '''Gets the definition of the specified word.
    '''
    word_range = DCSGetTermRangeInString(DICTIONARY, word, OFFSET)
    try:
        word_definition = DCSCopyTextDefinition(DICTIONARY, word, word_range)
    except IndexError as e:
        raise DefinitionNotFoundException('The definition not found.')

    return word_definition


class DefinitionNotFoundException(Exception):
    '''Custom exception for the "not found" error.
    '''
    pass


if __name__ == '__main__':
    word = get_stdin_string_stripped().decode(ENCODING)
    definition = get_dict_definition(word).encode(ENCODING)
    print(definition)
