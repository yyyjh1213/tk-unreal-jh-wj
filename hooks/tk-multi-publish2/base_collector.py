# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import os
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class BaseCollectorPlugin(HookBaseClass):
    """
    Base collector plugin class that provides common functionality for
    collecting items from the current session.
    """

    def process_current_session(self, settings, parent_item):
        """
        Base method for analyzing the current session and creating items to publish.
        Should be implemented by derived classes.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance
        """
        raise NotImplementedError

    def _get_icon_path(self, icon_name):
        """
        Helper method to get the full path to an icon.

        :param icon_name: The name of the icon file
        :returns: Full path to the icon
        """
        # get the icon path to display for this item
        icon_path = os.path.join(
            self.disk_location,
            "icons",
            icon_name
        )
        return icon_path

    def _create_session_item(self, session_type, display_name, parent_item, settings=None):
        """
        Helper method to create a session item with common properties.

        :param session_type: Type of the session (e.g., "maya.session", "unreal.session")
        :param display_name: Display name for the item
        :param parent_item: Parent Item instance
        :param settings: Optional settings dictionary
        :returns: Created session item
        """
        publisher = self.parent

        # create the session item for the publish hierarchy
        session_item = parent_item.create_item(
            session_type,
            "Session",
            display_name
        )

        # if a work template is configured, add it to the item properties
        if settings and "Work Template" in settings:
            work_template_setting = settings.get("Work Template")
            work_template = publisher.get_template_by_name(work_template_setting)
            if work_template:
                session_item.properties["work_template"] = work_template
                self.logger.debug("Work template defined for %s collection.", session_type)

        return session_item
