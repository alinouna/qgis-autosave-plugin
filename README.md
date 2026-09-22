# AutoSave — QGIS plugin

Saves your QGIS project and every editable vector layer on a timer, then puts the
layers straight back into edit mode so digitizing is never interrupted.

Built for long editing sessions where a crash or a forced close would otherwise
cost you everything since the last manual save.

## What it does

Every *N* minutes the plugin:

1. writes the project file, if the project has been saved to disk at least once
2. commits the pending edits of every layer currently in edit mode
3. reopens edit mode on each layer it committed, so you keep working

Results are reported in the QGIS message bar and written to the log panel
(`View ▸ Panels ▸ Log Messages`, under the **AutoSave** tab), including
per-layer commit errors when a layer cannot be saved.

## Installing

**From a release** — copy the `AutoSave` folder into your QGIS plugin directory:

| Platform | Path |
|---|---|
| Windows | `C:\Users\<you>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\` |
| Linux | `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/` |
| macOS | `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/` |

**From source**

```bash
git clone https://github.com/alinouna/qgis-autosave-plugin.git
cp -r qgis-autosave-plugin/AutoSave \
      ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
```

Then enable it under `Plugins ▸ Manage and Install Plugins ▸ Installed`.

The plugin folder must contain an `__init__.py` that exposes `classFactory`:

```python
def classFactory(iface):
    from .autosave import AutoSavePlugin
    return AutoSavePlugin(iface)
```

## Usage

Click the **AutoSave** toolbar icon to open the settings dialog:

- **Interval (minutes)** — how often to save, 1 to 1440
- **Enable automatic saving** — start or stop the timer

Settings persist between sessions in your QGIS profile (`AutoSave/interval` and
`AutoSave/enabled`), and the timer resumes automatically the next time QGIS
starts if it was left enabled.

## Translations

English and Italian ship in `resources/i18n/`. The plugin picks up your QGIS
display language automatically.

## Requirements

- QGIS 3.0 or newer, up to 4.99
- No external Python dependencies

## Project layout

```
AutoSave/
├── __init__.py                  entry point (classFactory)
├── autosave.py                  plugin logic
├── metadata.txt                 QGIS plugin metadata
├── ui/autosave_dialog.ui        settings dialog
└── resources/
    ├── i18n/                    .ts sources and compiled .qm
    └── images/                  toolbar icon and dialog preview
```

## License

[MIT](AutoSave/LICENSE) — Copyright (c) 2026 Ali Nouna

## Issues

Please report bugs and request features in the
[issue tracker](https://github.com/alinouna/qgis-autosave-plugin/issues).
