# Copyright (c) 2017 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import maya.cmds as cmds
import maya.mel as mel
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class MayaFBXPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an open maya session as an exported FBX.

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

        loader_url = "https://support.shotgunsoftware.com/hc/en-us/articles/219033078"

        return """
        <p>This plugin exports the Asset for the current session as an FBX file.
        The scene will be exported to the path defined by this plugin's configured 
        "Publish Template" setting.  The resulting FBX file can then be imported
        into Unreal Engine via the Loader.</p>
        """

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
        base_settings = super(MayaFBXPublishPlugin, self).settings or {}

        # settings specific to this class
        maya_publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            }
        }

        work_template_setting = {
            "Work Template": {
                "type": "template",
                "default": None,
                "description": "Template path for exported FBX files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            }
        }

        # update the base settings
        base_settings.update(maya_publish_settings)
        base_settings.update(work_template_setting)

        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["maya.fbx"]

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

        # if a publish template is configured, disable context change. This
        # is a temporary measure until the publisher handles context switching
        # natively.
        if settings.get("Publish Template").value:
            item.context_change_allowed = False

        path = _session_path()

        if not path:
            # the session has not been saved before (no path determined).
            # provide a save button. the session will need to be saved before
            # validation will succeed.
            self.logger.warn(
                "The Maya session has not been saved.",
                extra=_get_save_as_action()
            )

        self.logger.info(
            "Maya '%s' plugin accepted the current Maya session." %
            (self.name,)
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
        path = _session_path()

        # ---- ensure the session has been saved

        if not path:
            # the session still requires saving. provide a save button.
            # validation fails.
            error_msg = "The Maya session has not been saved."
            self.logger.error(
                error_msg,
                extra=_get_save_as_action()
            )
            raise Exception(error_msg)

        # ensure we have an updated project root
        project_root = cmds.workspace(q=True, rootDirectory=True)
        item.properties["project_root"] = project_root

        # log if no project root could be determined.
        if not project_root:
            self.logger.info(
                "Your session is not part of a maya project.",
                extra={
                    "action_button": {
                        "label": "Set Project",
                        "tooltip": "Set the maya project",
                        "callback": lambda: mel.eval('setProject ""')
                    }
                }
            )

        # ---- check the session against any attached work template

        # get the path in a normalized state. no trailing separator,
        # separators are appropriate for current os, no double separators,
        # etc.
        path = sgtk.util.ShotgunPath.normalize(path)

        # if the session item has a known work template, see if the path
        # matches. if not, warn the user and provide a way to save the file to
        # a different path
        work_template_setting = settings.get("Work Template")
        work_template = publisher.get_template_by_name(work_template_setting.value)
        if work_template:
            item.properties["work_template"] = work_template
            self.logger.debug(
                "Work template configured as {}.".format(work_template))
        else:
            self.logger.debug("No work template configured.")
            return False

        # ---- see if the version can be bumped post-publish

        # check to see if the next version of the work file already exists on
        # disk. if so, warn the user and provide the ability to jump to save
        # to that version now
        (next_version_path, version) = self._get_next_version_info(path, item)
        if next_version_path and os.path.exists(next_version_path):

            # determine the next available version_number. just keep asking for
            # the next one until we get one that doesn't exist.
            while os.path.exists(next_version_path):
                (next_version_path, version) = self._get_next_version_info(
                    next_version_path, item)

            error_msg = "The next version of this file already exists on disk."
            self.logger.error(
                error_msg,
                extra={
                    "action_button": {
                        "label": "Save to v%s" % (version,),
                        "tooltip": "Save to the next available version number, "
                                   "v%s" % (version,),
                        "callback": lambda: _save_session(next_version_path)
                    }
                }
            )
            raise Exception(error_msg)

        # ---- populate the necessary properties and call base class validation

        # populate the publish template on the item if found
        publish_template_setting = settings.get("Publish Template")
        publish_template = publisher.engine.get_template_by_name(
            publish_template_setting.value)
        if publish_template:
            item.properties["publish_template"] = publish_template
        else:
            self.logger.debug("No published template configured.")
            return False

        # set the session path on the item for use by the base plugin validation
        # step. NOTE: this path could change prior to the publish phase.
        item.properties["path"] = path

        # maya_path will be used for version numbering based on the Maya scene file
        item.properties["maya_path"] = path
        item.properties["publish_type"] = "Maya FBX"

        # run the base class validation
        return super(MayaFBXPublishPlugin, self).validate(settings, item)

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
        path = sgtk.util.ShotgunPath.normalize(_session_path())

        # ensure the session is saved
        _save_session(path)

        # Derive the work path from the work template
        work_path = _get_work_path(path, item.properties["work_template"])

        # Remove the filename from the work path
        path_components = os.path.split(work_path)
        destination_path = path_components[0]
        filename = path_components[1]

        # Ensure that the destination path exists before rendering the sequence
        self.parent.ensure_folder_exists(destination_path)

        # Replace file extension with .fbx
        fbx_name = os.path.splitext(filename)[0] + ".fbx"
        fbx_output_path = os.path.join(destination_path, fbx_name)
        
        # Export scene to FBX
        try:
            self.logger.info("Exporting scene to FBX {}".format(fbx_output_path))
            cmds.FBXResetExport()
            cmds.FBXExportSmoothingGroups('-v', True)
            # Mel script equivalent: mel.eval('FBXExport -f "fbx_output_path"')
            cmds.FBXExport('-f', fbx_output_path)
        except:
            self.logger.error("Could not export scene to FBX")
            return False

        # The file to publish is the FBX exported to the FBX output path
        item.properties["path"] = fbx_output_path
            
        # let the base class register the publish
        super(MayaFBXPublishPlugin, self).publish(settings, item)

    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once all the publish
        tasks have completed, and can for example be used to version up files.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        # do the base class finalization
        super(MayaFBXPublishPlugin, self).finalize(settings, item)

        # bump the session file to the next version
        self._save_to_next_version(item.properties["maya_path"], item, _save_session)

def _get_work_path(path, work_template):
    """
    Return the equivalent work path with the filename from path applied to the work template
    :param path: An absulote path with a filename
    :param work_template: A template to use to get the work path
    :returns a work path:
    """
    # Get the filename from the path
    filename = os.path.split(path)[1]
    
    # Retrieve the name field from the filename excluding the extension
    work_path_fields = {"name" : os.path.splitext(filename)[0]}
    
    # Apply the name to the work template
    work_path = work_template.apply_fields(work_path_fields)
    work_path = os.path.normpath(work_path)

    return work_path

def _session_path():
    """
    Return the path to the current session
    :return:
    """
    path = cmds.file(query=True, sn=True)

    if isinstance(path, unicode):
        path = path.encode("utf-8")

    return path


def _save_session(path):
    """
    Save the current session to the supplied path.
    """

    # Maya can choose the wrong file type so we should set it here
    # explicitly based on the extension
    maya_file_type = None
    if path.lower().endswith(".ma"):
        maya_file_type = "mayaAscii"
    elif path.lower().endswith(".mb"):
        maya_file_type = "mayaBinary"

    cmds.file(rename=path)

    # save the scene:
    if maya_file_type:
        cmds.file(save=True, force=True, type=maya_file_type)
    else:
        cmds.file(save=True, force=True)


# TODO: method duplicated in all the maya hooks
def _get_save_as_action():
    """
    Simple helper for returning a log action dict for saving the session
    """

    engine = sgtk.platform.current_engine()

    # default save callback
    callback = cmds.SaveScene

    # if workfiles2 is configured, use that for file save
    if "tk-multi-workfiles2" in engine.apps:
        app = engine.apps["tk-multi-workfiles2"]
        if hasattr(app, "show_file_save_dlg"):
            callback = app.show_file_save_dlg

    return {
        "action_button": {
            "label": "Save As...",
            "tooltip": "Save the current session",
            "callback": callback
        }
    }