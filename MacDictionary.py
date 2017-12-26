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
POPUP_TEMPLATE = '''
<h1><a href="''' + POPUP_HREF_PREFIX_OPEN + '''{word_escaped}">{word}</a></h1>
<p>{definition}</p>
<div class="close-wrapper">
<a class="close" href="''' + POPUP_HREF_CLOSE + '">' + chr(0x00D7) + '''</a>
</div>
'''
POPUP_BODY_MAX_LENGTH = 400
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


class MacDictionaryShowDefForSelectionCommand(sublime_plugin.TextCommand):
    '''A command which shows a word definition in a popup.
    '''

    def run(self, edit):
        if len(self.view.sel()) != 1:
            status_message(self.view, 'Please select only one region.')
            return

        region, word_raw = self._get_selected_region_info()
        word, definition = self._get_definition(word_raw)

        if not definition:
            status_message(self.view, 'No definition found.')
            return

        popup_info = {
            'data': {
                'word': word,
                'word_escaped': html.escape(word),
                'definition': html.escape(trim_string(definition,
                                                      POPUP_BODY_MAX_LENGTH)),
            },
            'location': region.end(),
        }

        self._show_popup(popup_info)

    def _get_selected_region_info(self):
        region = self.view.sel()[0]
        return (region, self.view.substr(region))

    def _get_definition(self, word):
        runner = MacDictionaryRunner()
        runner.run(word)

        if not runner.success:
            return None, None

        output = json.loads(runner.output)

        return output['word'], output['definition']

    def _show_popup(self, popup_info):
        if mdpopups.is_popup_visible(self.view):
            mdpopups.hide_popup(self.view)

        data = popup_info['data']
        content = POPUP_TEMPLATE.format(word=data['word'],
                                        word_escaped=data['word_escaped'],
                                        definition=data['definition'])

        mdpopups.show_popup(self.view,
                            content,
                            css=POPUP_CSS,
                            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                            location=popup_info['location'],
                            max_width=POPUP_MAX_WIDTH,
                            wrapper_class=POPUP_WRAPPER_CLASS,
                            on_navigate=self.on_popup_navigate)

    def on_popup_navigate(self, href):
        if href.startswith(POPUP_HREF_PREFIX_OPEN):
            word = href[len(POPUP_HREF_PREFIX_OPEN):]

            try:
                subprocess.check_call(['open', 'dict://{}'.format(word)])
            except subprocess.SubprocessError as e:
                message = 'Dictionary.app could not be opened.'
                status_message(self.view, message)

            mdpopups.hide_popup(self.view)
        elif href == POPUP_HREF_CLOSE:
            mdpopups.hide_popup(self.view)


class MacDictionaryRunner:
    '''Consults the MacOS dictionary.
    '''

    def run(self, word):
        popen_args = self._prepare_subprocess_args()

        try:
            process = subprocess.Popen(**popen_args)
            stdout, stderr = process.communicate(input=word.encode('utf-8'))
        except OSError as e:
            self.error = str(e)
            self.success = False
        else:
            self.output = stdout.decode('utf-8')
            self.error = stderr.decode('utf-8')
            self.success = True

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
        script = os.path.join(os.path.dirname(__file__),
                              'scripts',
                              'ConsultMacDictionary.py')
        return [SYSTEM_PYTHON, script]

    def _get_env(self):
        return os.environ.copy()


def status_message(view, message, ttl=4000):
    '''Shows the status message for the package.
    '''
    view.set_status(STATUS_KEY, 'MacDictinary: {}'.format(message))
    sublime.set_timeout(lambda: view.erase_status(STATUS_KEY), ttl)


def trim_string(string, max_length, ellipsis='...'):
    '''Trims a string.
    '''
    if string[max_length:]:
        return string[:max_length] + ellipsis
    else:
        return string[:max_length]
