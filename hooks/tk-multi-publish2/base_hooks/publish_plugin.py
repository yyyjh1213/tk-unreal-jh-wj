# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License. See LICENSE.md in the repo root for details about
# the license agreement.

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class PublishPlugin(HookBaseClass):
    """
    This class defines the required interface for a publish plugin. Publish
    plugins are responsible for operating on items collected by the collector
    plugin. Publish plugins define which items they will operate on as well as
    the execution logic for each phase of the publish process.
    """

    ############################################################################
    # Properties

    @property
    def name(self):
        """
        One line display name describing the plugin
        """
        raise NotImplementedError

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does
        """
        raise NotImplementedError

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        """
        return {}

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.
        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return []

    ############################################################################
    # Methods

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.
        """
        return {"accepted": True}

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        """
        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        raise NotImplementedError

    def finalize(self, settings, item):
        """
        Execute the finalize logic for the given item and settings.
        """
        pass
