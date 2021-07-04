# MacDictionary

A Sublime Text 3 / 4 package which provides a popup function for the macOS dictionary service.

![SublimeMacDictionary capture](https://raw.githubusercontent.com/gh640/SublimeMacDictionary/master/assets/images/capture.png)


## Dependencies

This package depends on [Sublime Markdown Popups (mdpopups)](https://github.com/facelessuser/sublime-markdown-popups/). You don't need to install it separately since it's automatically installed when you use [Package Control](https://packagecontrol.io/) to install this package.


## Installation

It's easy to install this package with [Package Control](https://packagecontrol.io/). If you haven't installed Package Control yet, first install it following the [instruction](https://packagecontrol.io/installation).

Once you've installed Pacakge Control, restart your Sublime Text and open the command palette (<kbd>ctrl/cmd + shift + p</kbd>). Then, find and select `Package Control: Install Package`. You will see `MacDictionary` in the list and select it.


## Usage

![SublimeMacDictionary animated capture](https://raw.githubusercontent.com/gh640/SublimeMacDictionary/master/assets/images/capture-animation.gif)

### Commands

This package provides the following commands.

- MacDictionary: Show definition (`mac_dictionary_show_def_for_selection`)
- MacDictionary: Switch brute mode (`mac_dictionary_brute_mode_switch`)

You can run these commands with the command palette (ctrl/cmd + shift + p).

Also you can set any custom key binding to run a command:

```json
[
  {
    "keys": ["shift+ctrl+d"],
    "command": "mac_dictionary_show_def_for_selection"
  }
]
```

### Context menu (right click menu)

Or, you can use the context menu item `Show definition` to open the definition popup.

### Brute mode

Additionally, you can use a mode named `brute_mode` with which the package tries to generate a popup aggressively every time when you move your mouse cursor. With the mode enabled, you don't need to call the command.

![SublimeMacDictionary animated capture for brute mode](https://raw.githubusercontent.com/gh640/SublimeMacDictionary/master/assets/images/capture-animation-brute_mode.gif)

The mode is disabled by default. You can enable it through the package settings:

```json
{
  "brute_mode": true
}
```

You can also use `MacDictionary: Switch brute mode` in the Command Palette to switch the `brute_mode`.

### Switching dictionaries

Although the macOS dictionary has a range of built-in and downloadable dictionaries, Apple unfortunately does not provide an API to the one that is used. Therefore, the package will return the first match from all enabled dictionaries. If you want to change that, you can do so with a workaround: In dictionary.app, open the preferences and drag your preferred dictionary (such as a thesaurus) to the top. You should see that it now has also moved to the leftmost position in the selection bar on top of the main app window.

After restarting sublime, the package will now use your new primary dictionary.

## License

Licensed under the MIT license.
