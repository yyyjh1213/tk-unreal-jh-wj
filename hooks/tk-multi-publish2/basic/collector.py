"""
Basic collector hook for Unreal Engine.
"""
import os
import sgtk
import unreal

HookBaseClass = sgtk.get_hook_baseclass()

class UnrealCollector(HookBaseClass):
    """
    Collector that operates on the current Unreal Editor session. Should
    collect and create publish items for assets and levels.
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
        Analyzes the current session open in Unreal Editor and parents a subtree
        of items under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance
        """
        # Create an item representing the current Unreal Editor session
        session_item = parent_item.create_item(
            "unreal.session",
            "Unreal Session",
            "Current Unreal Editor Session"
        )

        # Get the icon path to display for this item
        icon_path = os.path.join(
            self.disk_location,
            os.pardir,
            "icons",
            "unreal.png"
        )
        session_item.set_icon_from_path(icon_path)

        # Add selected assets
        self._collect_selected_assets(session_item)

    def _collect_selected_assets(self, parent_item):
        """
        Creates items for selected assets in the content browser.

        :param parent_item: Parent item instance
        """
        editor_util = unreal.EditorUtilityLibrary()
        selected_assets = editor_util.get_selected_assets()

        for asset in selected_assets:
            asset_path = asset.get_path_name()
            asset_name = asset.get_name()
            asset_class = asset.get_class().get_name()

            # Create the item
            item = parent_item.create_item(
                f"unreal.asset.{asset_class.lower()}",
                asset_class,
                asset_name
            )

            # Add properties for the publish plugins to use
            item.properties["asset_path"] = asset_path
            item.properties["asset_class"] = asset_class

            # Set the icon based on the asset type
            icon_path = os.path.join(
                self.disk_location,
                os.pardir,
                "icons",
                f"{asset_class.lower()}.png"
            )
            item.set_icon_from_path(icon_path)
