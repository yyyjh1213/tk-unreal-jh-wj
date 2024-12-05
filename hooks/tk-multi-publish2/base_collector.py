# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import glob
import os
import sys
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class UnrealCollectorPlugin(HookBaseClass):
    """
    Collector that operates on the current Unreal Editor session. Should
    inherit from the basic collector hook.
    """

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session open in Unreal and parents a subtree of
        items under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance

        """
        # create an item representing the current Unreal session
        item = self.collect_current_unreal_session(settings, parent_item)
        if not item:
            return

        # look at the render folder to find rendered images on disk
        self.collect_rendered_images(item)

        # look at the scene geometry to find meshes to publish
        self.collect_meshes(item)

    def collect_current_unreal_session(self, settings, parent_item):
        """
        Creates an item that represents the current Unreal session.

        :param dict settings: Configured settings for this collector
        :param parent_item: Parent Item instance

        :returns: Item of type unreal.session
        """

        publisher = self.parent

        # get the path to the current file
        path = unreal.Paths.get_project_file_path()

        # ensure the file path is normalized and append the filename
        path = sgtk.util.ShotgunPath.normalize(path)

        # display name for the item
        display_name = "Current Unreal Session"

        # create the session item for the publish hierarchy
        session_item = parent_item.create_item(
            "unreal.session",
            "Unreal Session",
            display_name
        )

        # get the icon path to display for this item
        icon_path = os.path.join(
            self.disk_location,
            "icons",
            "unreal.png"
        )

        # set the icon for the item
        session_item.set_icon_from_path(icon_path)

        # if a work template is configured, add it to the item properties so
        # that it can be used by attached publish plugins
        work_template_setting = settings.get("Work Template")
        if work_template_setting:

            work_template = publisher.get_template_by_name(work_template_setting)

            # store the template on the item for use by publish plugins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plugins will need to resolve the fields at
            # execution time.
            session_item.properties["work_template"] = work_template
            self.logger.debug("Work template defined for Unreal collection.")

        self.logger.info("Collected current Unreal scene")

        return session_item
