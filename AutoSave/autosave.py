# -*- coding: utf-8 -*-
# Copyright (C) 2026 Ali Nouna
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License.

import os
import traceback

from qgis.PyQt.QtCore import QTimer, QSettings, QCoreApplication, QTranslator, QLocale, Qt
from qgis.PyQt.QtWidgets import QAction, QDialog, QLabel, QSpinBox, QCheckBox
from qgis.PyQt.uic import loadUi
from qgis.PyQt.QtGui import QIcon, QPixmap

from qgis.core import QgsMessageLog, Qgis, QgsProject, QgsMapLayer


class AutoSavePlugin:

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        # Log QGIS version
        QgsMessageLog.logMessage(
            f"AutoSave plugin loaded. QGIS version: {Qgis.QGIS_VERSION}",
            "AutoSave",
            Qgis.Info
        )

        # Translation
        locale = QSettings().value("locale/userLocale", "en")[0:2]
        qm_path = os.path.join(
            self.plugin_dir,
            "resources",
            "i18n",
            f"AutoSave_{locale}.qm"
        )
        self.translator = None
        if os.path.exists(qm_path):
            self.translator = QTranslator()
            if self.translator.load(qm_path):
                QCoreApplication.installTranslator(self.translator)

        # Timer
        self.timer = QTimer(self.iface.mainWindow())
        self.timer.timeout.connect(self.do_autosave)

        # Settings
        self.settings = QSettings()
        self.interval_minutes = self.settings.value("AutoSave/interval", 5, int)
        self.enabled = self.settings.value("AutoSave/enabled", False, bool)

        QgsMessageLog.logMessage(
            f"Loaded settings: interval={self.interval_minutes}, enabled={self.enabled}",
            "AutoSave",
            Qgis.Info
        )

        # GUI
        self.action = None
        self.dialog = None
        self.spin_box = None
        self.check_box = None

        try:
            from . import resources_rc  # noqa: F401
        except ImportError:
            pass

    # --------------------------------------------------------------------------
    def tr(self, message: str) -> str:
        return QCoreApplication.translate("AutoSavePlugin", message)

    # --------------------------------------------------------------------------
    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "resources", "images", "icon.jpg")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(self.plugin_dir, "resources", "images", "icon.svg")

        self.action = QAction(
            QIcon(icon_path),
            self.tr("AutoSave – Automatic saving"),
            self.iface.mainWindow()
        )
        self.action.setStatusTip(
            self.tr("AutoSave - Automatically saves project and editable layers")
        )
        self.action.triggered.connect(self.open_dialog)

        self.iface.addPluginToMenu("AutoSave", self.action)
        self.iface.addToolBarIcon(self.action)

        if self.enabled:
            self.start_timer()
            self.iface.messageBar().pushSuccess(
                "AutoSave",
                self.tr("Automatic saving enabled every {minutes} minutes.")
                .format(minutes=self.interval_minutes)
            )

    def unload(self):
        self.stop_timer()
        if self.action:
            self.iface.removePluginMenu("AutoSave", self.action)
            self.iface.removeToolBarIcon(self.action)

    # --------------------------------------------------------------------------
    def open_dialog(self):
        if self.dialog is None:
            self.dialog = QDialog(self.iface.mainWindow())
            loadUi(self.plugin_path("ui/autosave_dialog.ui"), self.dialog)

            # ---- Find widgets ----
            self.spin_box = self.dialog.findChild(QSpinBox)
            self.check_box = self.dialog.findChild(QCheckBox)

            if self.spin_box:
                QgsMessageLog.logMessage(
                    f"Found spin box: {self.spin_box.objectName()} (value: {self.spin_box.value()})",
                    "AutoSave",
                    Qgis.Info
                )
            else:
                QgsMessageLog.logMessage(
                    "No QSpinBox found!",
                    "AutoSave",
                    Qgis.Warning
                )

            if self.check_box:
                QgsMessageLog.logMessage(
                    f"Found check box: {self.check_box.objectName()} (checked: {self.check_box.isChecked()})",
                    "AutoSave",
                    Qgis.Info
                )
            else:
                QgsMessageLog.logMessage(
                    "No QCheckBox found!",
                    "AutoSave",
                    Qgis.Warning
                )

            # ---- Preview image ----
            img_path_jpg = os.path.join(self.plugin_dir, "resources", "images", "preview.jpg")
            img_path_png = os.path.join(self.plugin_dir, "resources", "images", "preview.png")
            img_path_svg = os.path.join(self.plugin_dir, "resources", "images", "preview.svg")
            img_path = None

            if os.path.exists(img_path_jpg):
                img_path = img_path_jpg
            elif os.path.exists(img_path_png):
                img_path = img_path_png
            elif os.path.exists(img_path_svg):
                img_path = img_path_svg

            if img_path:
                pixmap = QPixmap(img_path)
                if not pixmap.isNull():
                    # Correct enums for PyQt6 / QGIS 4
                    pixmap = pixmap.scaled(
                        400, 160,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    label = QLabel()
                    label.setPixmap(pixmap)
                    label.setAlignment(Qt.AlignmentFlag.AlignCenter)   # FIXED HERE
                    label.setStyleSheet("margin: 10px;")
                    layout = self.dialog.layout()
                    if layout:
                        layout.insertWidget(0, label)
                else:
                    self.iface.messageBar().pushWarning(
                        "AutoSave",
                        self.tr("Could not load preview image.")
                    )

            # ---- Set current values ----
            if self.spin_box:
                self.spin_box.setValue(self.interval_minutes)
            if self.check_box:
                self.check_box.setChecked(self.enabled)

            # ---- Connect signals ----
            if hasattr(self.dialog, 'buttonBox'):
                self.dialog.buttonBox.accepted.connect(self.apply_settings)
                self.dialog.buttonBox.rejected.connect(self.dialog.close)
                QgsMessageLog.logMessage("Connected buttonBox.accepted", "AutoSave", Qgis.Info)
            else:
                self.dialog.accepted.connect(self.apply_settings)
                QgsMessageLog.logMessage("Connected dialog.accepted", "AutoSave", Qgis.Info)

        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    # --------------------------------------------------------------------------
    def apply_settings(self):
        QgsMessageLog.logMessage("apply_settings() called!", "AutoSave", Qgis.Info)

        # Read values
        if self.spin_box:
            new_interval = self.spin_box.value()
        else:
            new_interval = 5

        if self.check_box:
            new_enabled = self.check_box.isChecked()
        else:
            new_enabled = False

        QgsMessageLog.logMessage(
            f"apply_settings: interval={new_interval}, enabled={new_enabled}",
            "AutoSave",
            Qgis.Info
        )

        self.interval_minutes = new_interval
        self.enabled = new_enabled

        # Save settings
        self.settings.setValue("AutoSave/interval", self.interval_minutes)
        self.settings.setValue("AutoSave/enabled", self.enabled)

        # Restart timer
        self.timer.stop()
        if self.interval_minutes < 1:
            self.interval_minutes = 1
        self.timer.start(self.interval_minutes * 60 * 1000)

        QgsMessageLog.logMessage(
            f"AutoSave timer restarted ({self.interval_minutes} minutes).",
            "AutoSave",
            Qgis.Info
        )

        if self.enabled:
            self.iface.messageBar().pushSuccess(
                "AutoSave",
                self.tr("Automatic saving enabled every {minutes} minutes.")
                .format(minutes=self.interval_minutes)
            )
        else:
            self.iface.messageBar().pushWarning(
                "AutoSave",
                self.tr("Automatic saving disabled.")
            )

        self.dialog.close()

    # --------------------------------------------------------------------------
    def start_timer(self):
        if self.interval_minutes < 1:
            self.interval_minutes = 1
        self.timer.stop()
        self.timer.start(self.interval_minutes * 60 * 1000)
        QgsMessageLog.logMessage(
            f"AutoSave timer started ({self.interval_minutes} minutes).",
            "AutoSave",
            Qgis.Info
        )

    def stop_timer(self):
        if self.timer.isActive():
            self.timer.stop()
            QgsMessageLog.logMessage(
                "AutoSave timer stopped.",
                "AutoSave",
                Qgis.Info
            )

    # --------------------------------------------------------------------------
    def do_autosave(self):
        project = QgsProject.instance()
        saved_layers = 0
        failed_layers = 0
        log_parts = []

        # ---- Save project ----
        if project.fileName():
            try:
                project.write()
                log_parts.append(self.tr("Project saved."))
            except Exception as e:
                log_parts.append(self.tr("Error saving project: {error}").format(error=str(e)))
                QgsMessageLog.logMessage(
                    f"Project save error: {traceback.format_exc()}",
                    "AutoSave",
                    Qgis.Critical
                )
        else:
            log_parts.append(self.tr("Project not saved (no file path)."))

        # ---- Save editable vector layers ----
        for layer in project.mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer and layer.isEditable():
                try:
                    if layer.commitChanges():
                        layer.startEditing()
                        saved_layers += 1
                    else:
                        failed_layers += 1
                        errors = layer.commitErrors()
                        if errors:
                            error_msgs = "; ".join([str(e) for e in errors])
                        else:
                            error_msgs = "Unknown error (commitErrors returned empty)"
                        log_parts.append(
                            self.tr("Failed to save layer: {name} ({error})")
                            .format(name=layer.name(), error=error_msgs)
                        )
                except Exception as e:
                    failed_layers += 1
                    log_parts.append(
                        self.tr("Exception while saving layer {name}: {error}")
                        .format(name=layer.name(), error=str(e))
                    )
                    QgsMessageLog.logMessage(
                        f"Layer save exception: {traceback.format_exc()}",
                        "AutoSave",
                        Qgis.Critical
                    )

        if saved_layers > 0:
            log_parts.append(self.tr("{count} layer(s) saved.").format(count=saved_layers))
        if failed_layers > 0:
            log_parts.append(self.tr("{count} layer(s) failed.").format(count=failed_layers))

        full_msg = " ".join(log_parts)
        if full_msg:
            QgsMessageLog.logMessage(full_msg, "AutoSave", Qgis.Info)
            self.iface.messageBar().pushInfo("AutoSave", full_msg)

    # --------------------------------------------------------------------------
    def plugin_path(self, relative_path: str) -> str:
        return os.path.join(self.plugin_dir, relative_path)


# ------------------------------------------------------------------------------
def classFactory(iface):
    return AutoSavePlugin(iface)
