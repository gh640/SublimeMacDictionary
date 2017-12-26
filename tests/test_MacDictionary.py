# coding: utf-8

'''Tests ConsultMacDictionary.py.
'''

import io
import json
import sys
from contextlib import contextmanager

import sublime

import unittest


MacDictionary = sys.modules['MacDictionary.MacDictionary']


class TestMacDictionaryRunner(unittest.TestCase):
    '''Tests MacDictionaryRunner.
    '''

    def test_simple_words(self):
        runner = MacDictionary.MacDictionaryRunner()
        runner.run('word')

        self.assertTrue(runner.success)
        self.assertNotEquals(runner.output, '')
        self.assertFalse(hasattr(runner, 'error'))

        output = json.loads(runner.output)

        self.assertTrue('word' in output)
        self.assertTrue('definition' in output)

        self.assertEquals(output['word'], 'word')
        self.assertIn('word', output['definition'])

    def test_empty_word(self):
        runner = MacDictionary.MacDictionaryRunner()
        runner.run('')

        self.assertFalse(runner.success)
        self.assertFalse(hasattr(runner, 'output'))
        self.assertNotEqual(runner.error, '')

    def test_undefined_word(self):
        runner = MacDictionary.MacDictionaryRunner()
        runner.run('🐙')

        self.assertFalse(runner.success)
        self.assertFalse(hasattr(runner, 'output'))
        self.assertNotEqual(runner.error, '')


class TestHelperFunctionStatusMessage(unittest.TestCase):
    '''Tests status_message().
    '''

    def setUp(self):
        self.view = sublime.active_window().new_file()

    def tearDown(self):
        if self.view:
            self.view.set_scratch(True)
            self.view.window().focus_view(self.view)
            self.view.window().run_command('close_file')

    def test_status_message(self):
        message = 'sample message'

        with self.redirect_stdout():
            MacDictionary.status_message(self.view, message)
            message_set = self.view.get_status('mac-dictionary-definition')

            self.assertEqual(message_set, 'MacDictionary: {}'.format(message))
            s = sys.stdout.getvalue()
            self.assertEqual(s, message + '\n')

    @contextmanager
    def redirect_stdout(self):
        sys.stdout = io.StringIO()
        yield
        sys.stdout = sys.__stdout__


class TestHelperFunctionTrim(unittest.TestCase):
    '''Tests trim().
    '''

    def test_trim(self):
        self.assertEqual(MacDictionary.trim('apple', 10), 'apple')
        self.assertEqual(MacDictionary.trim('apple', 3), 'app...')
        self.assertEqual(MacDictionary.trim('apple', 2, '・・・'), 'ap・・・')
