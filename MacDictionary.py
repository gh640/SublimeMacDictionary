# coding: utf-8

'''A Sublime Text 3 package which shows a word definition in a popup.
'''

import html
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

import sublime
import sublime_plugin

import mdpopups


SYSTEM_PYTHON = '/usr/bin/python2.7'
PHANTOM_KEY = 'mac-dictionary-definition'
PHANTOM_WRAPPER_CLASS = 'mac-dictionary-definition'
PHANTOM_HREF_PREFIX_OPEN = 'open-dict-app:'
PHANTOM_HREF_CLOSE = 'close'
PHANTOM_TEMPLATE = '''
<h1><a href="''' + PHANTOM_HREF_PREFIX_OPEN + '''{word_escaped}">{word}</a></h1>
<p>{definition}</p>
<a class="close" href="''' + PHANTOM_HREF_CLOSE + '">' + chr(0x00D7) + '''</a>
'''
PHANTOM_BODY_MAX_LENGTH = 300
PHANTOM_CSS = '''
<style>
    body {
        margin: 0;
        padding: 0;
    }
    .mac-dictionary-definition {
        font-size: 12px;
        line-height: 20px;
        padding: 0 18px 10px 10px;
        width: 400px;
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

    .mac-dictionary-definition .close {
        background-color: var(--mdpopups-admon-error-bg);
        color: var(--mdpopups-admon-error-fg);
        padding: 1px 6px;
        text-decoration: none;
    }
</style>
'''
THREAD_MAX_WORKERS = 5


class MacDictionaryShowDefsForSelectionCommand(sublime_plugin.TextCommand):
    '''A command which shows word definitions in popups.
    '''

    def run(self, edit):
        region_infos = self._get_selected_region_infos()
        self.phantom_set = sublime.PhantomSet(self.view, PHANTOM_KEY)

        definition_infos = self._get_definitions(region_infos)

        popup_infos = [{
            'data': {
                'word': word,
                'word_escaped': html.escape(word),
                'definition': html.escape(trim_string(definition, PHANTOM_BODY_MAX_LENGTH)),
            },
            'region': self.view.line(region),
        } for region, word, definition in definition_infos]

        self._show_phantoms(popup_infos)

    def _get_selected_region_infos(self):
        selection = self.view.sel()

        return [(region, self.view.substr(region)) for region in selection]

    def _get_definitions(self, region_infos):
        with ThreadPoolExecutor(max_workers=THREAD_MAX_WORKERS) as executor:
            futures = [executor.submit(self._get_definition, region_info)
                       for region_info in region_infos]
            definitions = []

            for future in as_completed(futures):
                try:
                    result = future.result()
                    region, word, definition = result
                    if definition:
                        definitions.append(result)
                except Exception as e:
                    pass

            return definitions

    def _get_definition(self, region_info):
        region, word = region_info

        runner = MacDictionaryRunner()
        runner.run(word)

        if not runner.success:
            return region, word, None

        return region, word, runner.output

    def _show_phantoms(self, popup_infos):
        mdpopups.erase_phantoms(self.view, PHANTOM_KEY)

        for popup_info in popup_infos:
            data = popup_info['data']
            content = PHANTOM_TEMPLATE.format(word=data['word'],
                                              word_escaped=data['word_escaped'],
                                              definition=data['definition'])

            mdpopups.add_phantom(self.view,
                                 PHANTOM_KEY,
                                 popup_info['region'],
                                 content,
                                 sublime.LAYOUT_BELOW,
                                 css=PHANTOM_CSS,
                                 wrapper_class=PHANTOM_WRAPPER_CLASS,
                                 on_navigate=self.on_phantom_navigate)

    def on_phantom_navigate(self, href):
        if href.startswith(PHANTOM_HREF_PREFIX_OPEN):
            word = href[len(PHANTOM_HREF_PREFIX_OPEN):]
            subprocess.Popen(['open', 'dict://{}'.format(word)])
            mdpopups.erase_phantoms(self.view, PHANTOM_KEY)
        elif href == PHANTOM_HREF_CLOSE:
            mdpopups.erase_phantoms(self.view, PHANTOM_KEY)


class MacDictionaryClearDefsForSelectionCommand(sublime_plugin.TextCommand):
    '''A command which clears the popups.
    '''

    def run(self, edit):
        mdpopups.erase_phantoms(self.view, PHANTOM_KEY)


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
        script = os.path.join(os.path.dirname(__file__), 'scripts', 'ConsultMacDictionary.py')
        return [SYSTEM_PYTHON, script]

    def _get_env(self):
        return os.environ.copy()


def trim_string(string, max_length, ellipsis='...'):
    '''Trims a string.
    '''
    if string[max_length:]:
        return string[:max_length] + ellipsis
    else:
        return string[:max_length]
