# coding: utf-8

'''A Sublime Text 3 package which shows a word definition in a popup.
'''

import html
import json
import os
import subprocess

import sublime
import sublime_plugin

import mdpopups


SYSTEM_PYTHON = '/usr/bin/python2.7'
STATUS_KEY = 'mac-dictionary-definition'
POPUP_WRAPPER_CLASS = 'mac-dictionary-definition'
POPUP_HREF_PREFIX_OPEN = 'open-dict-app:'
POPUP_HREF_CLOSE = 'close'
POPUP_TEMPLATE = (
    '''
<h1><a href="'''
    + POPUP_HREF_PREFIX_OPEN
    + '''{word_escaped}">{word}</a></h1>
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
POPUP_CSS = '''
body {
    margin: 0;
    padding: 0;
}
.mac-dictionary-definition {
    font-size: 12px;
    line-height: 20px;
    padding: 0 18px 10px 10px;
}

.mac-dictionary-definition h1 {
    background-color: var(--mdpopups-admon-success-bg);
    color: var(--mdpopups-admon-success-title-fg);
    font-size: 12px;
    line-height: 12px;
    margin: 0 -18px 10px -10px;
    padding: 10px;
}
.mac-dictionary-definition p {
    margin: 6px 0;
}

.mac-dictionary-definition .close-wrapper {
    margin-top: 20px;
}

.mac-dictionary-definition .close {
    background-color: var(--mdpopups-admon-error-bg);
    color: var(--mdpopups-admon-error-fg);
    font-size: 10px;
    padding: 1px 6px;
    text-decoration: none;
}
'''
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

        popup = MacDictionaryPopup(view)
        word, definition = popup.get_definition(word_raw)
        if not definition:
            return

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

        popup = MacDictionaryPopup(self.view)
        word, definition = popup.get_definition(word_raw)
        if not definition:
            return

        popup.show_popup(region, word, definition)

    def _get_selected_region_info(self):
        region = self.view.sel()[0]

        return (region, self.view.substr(region))


class MacDictionaryPopup:
    def __init__(self, view):
        self.view = view

    def get_definition(self, word):
        runner = MacDictionaryRunner()
        runner.run(word)

        if not runner.success:
            status_message(self.view, runner.error)
            return None, None

        output = json.loads(runner.output)

        return output['word'], output['definition']

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
        if mdpopups.is_popup_visible(self.view):
            mdpopups.hide_popup(self.view)

        data = popup_info['data']
        content = POPUP_TEMPLATE.format(
            word=data['word'],
            word_escaped=data['word_escaped'],
            definition=data['definition'],
        )

        mdpopups.show_popup(
            self.view,
            content,
            css=POPUP_CSS,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            location=popup_info['location'],
            max_width=POPUP_MAX_WIDTH,
            wrapper_class=POPUP_WRAPPER_CLASS,
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

            mdpopups.hide_popup(self.view)
        elif href == POPUP_HREF_CLOSE:
            mdpopups.hide_popup(self.view)

    def _escape(self, string):
        return html.escape(string, False)


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


class MacDictionaryBruteModeSwitchCommand(sublime_plugin.WindowCommand):
    '''A command which allow for switching the `brute_mode` setting.'''

    OPTIONS = (['on', 'On'], ['off', 'Off'])
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
