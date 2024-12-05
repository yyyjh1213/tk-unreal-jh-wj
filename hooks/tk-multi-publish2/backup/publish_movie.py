# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import os
import pprint
import sys
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class UnrealMoviePublishPlugin(HookBaseClass):
    """
    Plugin for publishing an open unreal session.

    This hook relies on functionality found in the base file publisher hook in
    the publish2 app and should inherit from it in the configuration. The hook
    setting for this plugin should look something like this::

        hook: "{self}/publish_file.py:{engine}/tk-multi-publish2/basic/publish_session.py"

    """

    # NOTE: The plugin icon and name are defined by the base file plugin.

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """

        loader_url = "https://help.autodesk.com/view/SGSUB/ENU/?guid=SG_Supervisor_Artist_sa_integrations_sa_integrations_user_guide_html"

        return """
        Publishes the file to Flow Production Tracking. A <b>Publish</b> entry will be
        created in Flow Production Tracking which will include a reference to the file's current
        path on disk. If a publish template is configured, a copy of the current session
        will be copied to the publish template path which will be the file that is
        published. Other users will be able to access the published file via
        the <b>Loader</b> so long as they have access to
        the file's location on disk.

        If the session has not been saved, validation will fail and a button
        will be provided in the logging output to save the file.

        <h3>File versioning</h3>
        If the filename contains a version number, the process will bump the
        file to the next version after publishing.

        The <b>Loader</b> can be used to load published files. See the Loader
        documentation for more information.

        <a href='%s'>The Flow Production Tracking Plugin Publisher Guide</a>

        """ % (loader_url,)

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate, publish and
        finalize methods.

        A dictionary on the following form::

            {
                "Settings Name": {
                    "type": "settings_type",
                    "default": "default_value",
                    "description": "One line description of the setting"
            }

        The type string should be one of the data types that toolkit accepts as
        part of its environment configuration.
        """

        # inherit the settings from the base publish plugin
        base_settings = super(UnrealMoviePublishPlugin, self).settings or {}

        # settings specific to this class
        unreal_publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                             "correspond to a template defined in "
                             "templates.yml.",
            }
        }

        # update the base settings
        base_settings.update(unreal_publish_settings)

        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["unreal.movie"]

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.

        A publish task will be generated for each item accepted here. Returns a
        dictionary with the following booleans:

            - accepted: Indicates if the plugin is interested in this value at
                all. Required.
            - enabled: If True, the plugin will be enabled in the UI, otherwise
                it will be disabled. Optional, True by default.
            - visible: If True, the plugin will be visible in the UI, otherwise
                it will be hidden. Optional, True by default.
            - checked: If True, the plugin will be checked in the UI, otherwise
                it will be unchecked. Optional, True by default.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process

        :returns: dictionary with boolean keys accepted, required and enabled
        """

        path = item.properties.get("path", "")

        # if a publish template is configured, disable context change. This
        # is a temporary measure until the publisher handles context switching
        # natively.
        if settings.get("Publish Template").value:
            item.context_change_allowed = False

        self.logger.debug(
            "Unreal '%s' plugin accepted the path: %s" % (self.name, path),
        )
        return {
            "accepted": True,
            "checked": True
        }

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish. Returns a
        boolean to indicate validity.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: True if item is valid, False otherwise.
        """

        publisher = self.parent
        path = item.properties.get("path", "")

        # ---- determine the information required to validate

        # ---- check that our session has not changed
        if not os.path.exists(path):
            self.logger.error(
                "The path '%s' no longer exists!" % (path,),
            )
            return False

        # get the configured work file template
        work_template = item.properties.get("work_template")
        publish_template = publisher.get_template_by_name(settings.get("Publish Template").value)

        # ---- validate work template

        self.logger.debug("Work template: %s" % work_template)
        self.logger.debug("Publish template: %s" % publish_template)

        # ---- populate the necessary template fields

        # get the fields from the path
        path_fields = work_template.get_fields(path)

        # ensure all work template fields are present in the path
        missing_keys = publish_template.missing_keys(path_fields)
        if missing_keys:
            self.logger.warning(
                "Work file '%s' missing keys required for the publish "
                "template: %s" % (path, missing_keys)
            )
            return False

        # create the publish path by applying the fields. store it in the item's
        # properties. This is the path we'll create and then publish in the base
        # publish plugin. Also set the publish_path to be explicit.
        item.properties["path"] = publish_template.apply_fields(path_fields)
        item.properties["publish_path"] = item.properties["path"]

        # use the work file's version number when publishing
        if "version" in path_fields:
            item.properties["publish_version"] = path_fields["version"]

        # run the base class validation
        return super(UnrealMoviePublishPlugin, self).validate(settings, item)

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        # get the path in a normalized state. no trailing separator, separators
        # are appropriate for current os, no double separators, etc.
        path = sgtk.util.ShotgunPath.normalize(item.properties["path"])

        # ensure the session is saved
        _save_session(path)

        # update the item with the saved session path
        item.properties["path"] = path

        # add dependencies for the base class to register when publishing
        item.properties["publish_dependencies"] = \
            [item.properties["path"]]

        # let the base class register the publish
        super(UnrealMoviePublishPlugin, self).publish(settings, item)


def _save_session(path):
    """
    Save the current session to the supplied path.
    """

    # Ensure that the folder exists
    folder = os.path.dirname(path)
    ensure_folder_exists(folder)

    return True


def ensure_folder_exists(path):
    """
    Create the folder if it doesn't exist
    """
    if not os.path.exists(path):
        os.makedirs(path)
