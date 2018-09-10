# MacDictionary

A Sublime Text 3 package which provides a popup function for the MacOS dictionary service.

![SublimeMacDictionary capture](https://raw.githubusercontent.com/gh640/SublimeMacDictionary/master/assets/images/capture.png)


## Dependencies

This package depends on [Sublime Markdown Popups (mdpopups)](https://github.com/facelessuser/sublime-markdown-popups/). You don't need to install it separately since it's automatically installed when you use [Package Control](https://packagecontrol.io/) to install this package.


## Installation

It's easy to install this package with [Package Control](https://packagecontrol.io/). If you haven't installed Package Control yet, first install it following the [instruction](https://packagecontrol.io/installation).

Once you've installed Pacakge Control, restart your Sublime Text and open the command palette (<kbd>ctrl/cmd + shift + p</kbd>). Then, find and select `Package Control: Install Package`. You will see `MacDictionary` in the list and select it.


## Usage

![SublimeMacDictionary animated capture](https://raw.githubusercontent.com/gh640/SublimeMacDictionary/master/assets/images/capture-animation.gif)

### Commands

This package provides the following command.

- MacDictionary: Show definition

You can run a command with the command palette (ctrl/cmd + shift + p).

### Context menu (right click menu)

Or, you can use the context menu item `Show definition` to open the definition popup.

### Brute mode

Additionally, you can use a mode named `brute_mode` with which the package tries to generate a popup aggressively every time when you move your mouse cursor. With the mode enabled, you don't need to call the command.

![SublimeMacDictionary animated capture for brute mode](https://raw.githubusercontent.com/gh640/SublimeMacDictionary/master/assets/images/capture-animation-brute_mode.gif)

Of course, the mode is disabled by default. You can enable it through the package settings:

```json
{
  "brute_mode": true
}
```

## License

Licensed under the MIT license.
