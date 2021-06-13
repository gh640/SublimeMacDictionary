# coding: utf-8

'''A Sublime Text 3 / 4 package which shows a word definition in a popup.
'''

import html
import json
import os
import subprocess

import sublime
import sublime_plugin

SYSTEM_PYTHON = '/usr/bin/python2.7'
STATUS_KEY = 'mac-dictionary-definition'
POPUP_HREF_PREFIX_OPEN = 'open-dict-app:'
POPUP_HREF_CLOSE = 'close'
POPUP_TEMPLATE = (
    '''
<p><a href="'''
    + POPUP_HREF_PREFIX_OPEN
    + '''{word_escaped}">{word}</a></p>
<p>{definition}</p>
<div class="close-wrapper">
<a class="close" href="'''
    + POPUP_HREF_CLOSE
    + '">'
    + chr(0x00D7)
    + '''</a>
</div>
'''
)
POPUP_BODY_MAX_LEN = 400
POPUP_MAX_WIDTH = 400


class MacDictionaryBruteEventListener(sublime_plugin.EventListener):
    '''An event listener which shows the word definition popup.'''

    def on_hover(self, view, point, hover_zone):
        settings = load_settings()
        if not settings.get('brute_mode'):
            return

        region = view.word(point)
        word_raw = view.substr(region)
        if not word_raw:
            return

        try:
            word, definition = get_definition(word_raw)
        except MacDictionaryError as e:
            status_message(view, e.args[0])
            return
            
        if not definition:
            return

        popup = MacDictionaryPopup(view)
        popup.show_popup(region, word, definition)


class MacDictionaryShowDefForSelectionCommand(sublime_plugin.TextCommand):
    '''A command which shows a word definition in a popup.'''

    def run(self, edit):
        if len(self.view.sel()) != 1:
            status_message(self.view, 'Please select only one region.')
            return

        region, word_raw = self._get_selected_region_info()

        if region.empty():
            status_message(self.view, 'The selected text is empty.')
            return

        try:
            word, definition = get_definition(word_raw)
        except MacDictionaryError as e:
            status_message(self.view, e.args[0])
            return

        if not definition:
            return

        popup = MacDictionaryPopup(self.view)
        popup.show_popup(region, word, definition)


    def _get_selected_region_info(self):
        region = self.view.sel()[0]

        return (region, self.view.substr(region))


class MacDictionaryPopup:
    '''Controls popup windows.'''
    def __init__(self, view):
        self.view = view

    def show_popup(self, region, word, definition):
        popup_info = self._prepare_popup_info(region, word, definition)
        self._do_show_popup(popup_info)

    def _prepare_popup_info(self, region, word, definition):
        data = {
            'word': word,
            'word_escaped': self._escape(word),
            'definition': self._escape(trim(definition, POPUP_BODY_MAX_LEN)),
        }
        return {'data': data, 'location': region.end()}

    def _do_show_popup(self, popup_info):
        if self.view.is_popup_visible():
            self.view.hide_popup()

        data = popup_info['data']
        content = POPUP_TEMPLATE.format(
            word=data['word'],
            word_escaped=data['word_escaped'],
            definition=data['definition'],
        )

        self.view.show_popup(
            content,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            location=popup_info['location'],
            max_width=POPUP_MAX_WIDTH,
            on_navigate=self.on_popup_navigate,
        )

    def on_popup_navigate(self, href):
        if href.startswith(POPUP_HREF_PREFIX_OPEN):
            word = href[len(POPUP_HREF_PREFIX_OPEN) :]

            try:
                subprocess.check_call(['open', 'dict://{}'.format(word)])
            except subprocess.SubprocessError as e:
                message = 'Dictionary.app could not be opened.'
                status_message(self.view, message)

            self.view.hide_popup()
        elif href == POPUP_HREF_CLOSE:
            self.view.hide_popup()

    def _escape(self, string):
        return html.escape(string, False)


def get_definition(word):
    '''Gets the definition of word.'''
    runner = MacDictionaryRunner()
    runner.run(word)

    if not runner.success:
        raise MacDictionaryError(runner.error)

    output = json.loads(runner.output)

    return output['word'], output['definition']


class MacDictionaryRunner:
    '''Consults the MacOS dictionary.'''

    def run(self, word):
        popen_args = self._prepare_subprocess_args()

        try:
            process = subprocess.Popen(**popen_args)
            stdout, stderr = process.communicate(input=word.encode('utf-8'))
        except subprocess.SubprocessError as e:
            self.error = str(e)
            self.success = False
        else:
            if process.returncode == 0:
                self.output = stdout.decode('utf-8')
                self.success = True
            else:
                self.error = stderr.decode('utf-8')
                self.success = False

    def _prepare_subprocess_args(self):
        popen_args = {
            'args': self._get_cmd(),
            'env': self._get_env(),
            'stdin': subprocess.PIPE,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
        }

        return popen_args

    def _get_cmd(self):
        script = os.path.join(
            os.path.dirname(__file__), 'scripts', 'ConsultMacDictionary.py'
        )
        return [SYSTEM_PYTHON, script]

    def _get_env(self):
        return os.environ.copy()


class MacDictionaryError(Exception):
    '''Custom error class.'''
    pass


class MacDictionaryBruteModeSwitchCommand(sublime_plugin.WindowCommand):
    '''A command which allow for switching the `brute_mode` setting.'''

    OPTIONS = (['on', 'Brute mode on'], ['off', 'Brute mode off'])
    SETTING_VALUE_MAP = (True, False)

    def run(self):
        self.window.show_quick_panel(self.OPTIONS, self.switch)

    def switch(self, form_index):
        if form_index < 0:
            return

        settings = load_settings()
        settings.set('brute_mode', self._map_index_to_value(form_index))
        save_settings()
        status_message(
            self.window.active_view(),
            'Brute mode switched {}.'.format(self.OPTIONS[form_index][1]),
        )

    def _map_index_to_value(self, form_index):
        return self.SETTING_VALUE_MAP[form_index]


def load_settings():
    return sublime.load_settings('MacDictionary.sublime-settings')


def save_settings():
    sublime.save_settings('MacDictionary.sublime-settings')


def status_message(view, message, ttl=4000):
    '''Shows the status message for the package.'''
    print(message)
    view.set_status(STATUS_KEY, 'MacDictionary: {}'.format(message))
    sublime.set_timeout(lambda: view.erase_status(STATUS_KEY), ttl)


def trim(string, max_length, ellipsis='...'):
    '''Trims a string.'''
    if string[max_length:]:
        return string[:max_length] + ellipsis
    else:
        return string[:max_length]
