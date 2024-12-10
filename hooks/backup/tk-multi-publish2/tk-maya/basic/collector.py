"""
Basic collector hook for Maya in Unreal Engine context.
"""
import os
import sgtk
import maya.cmds as cmds

HookBaseClass = sgtk.get_hook_baseclass()

class MayaUnrealCollector(HookBaseClass):
    """
    Collector that operates on the current Maya session for Unreal Engine.
    """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this collector expects to receive
        through the settings parameter in the process_current_session and
        process_file methods.
        """
        return {
            "Work Template": {
                "type": "template",
                "default": None,
                "description": "Template path for work files. Should correspond to a template defined in templates.yml."
            },
        }

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session open in Maya and parents a subtree
        of items under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance
        """
        # Create an item representing the current Maya session
        session_item = parent_item.create_item(
            "maya.session",
            "Maya Session",
            "Current Maya Session"
        )

        # Get the icon path to display for this item
        icon_path = os.path.join(
            self.disk_location,
            os.pardir,
            "icons",
            "maya.png"
        )
        session_item.set_icon_from_path(icon_path)

        # Add selected assets
        self._collect_selected_assets(session_item)

    def _collect_selected_assets(self, parent_item):
        """
        Creates items for selected assets in the Maya scene.

        :param parent_item: Parent item instance
        """
        selected_nodes = cmds.ls(selection=True)

        for node in selected_nodes:
            node_name = cmds.ls(node, shortNames=True)[0]
            node_type = cmds.nodeType(node)

            # Create the item
            item = parent_item.create_item(
                f"maya.asset.{node_type.lower()}",
                node_type,
                node_name
            )

            # Add properties for the publish plugins to use
            item.properties["node_name"] = node_name
            item.properties["node_type"] = node_type

            # Set the icon based on the node type
            icon_path = os.path.join(
                self.disk_location,
                os.pardir,
                "icons",
                f"{node_type.lower()}.png"
            )
            item.set_icon_from_path(icon_path)
