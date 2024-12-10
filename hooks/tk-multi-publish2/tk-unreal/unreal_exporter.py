"""
Hook for exporting assets from Unreal Engine.
"""
import sgtk
import unreal

HookBaseClass = sgtk.get_hook_baseclass()

class UnrealExporter(HookBaseClass):
    """
    Hook for exporting assets from Unreal Engine.
    """

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.
        """
        return ["unreal.asset"]

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin.
        
        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: dictionary with the following keys:
            - accepted (bool): Indicates if the plugin is interested in this value
            - enabled (bool): If True, the plugin will be enabled in the UI,
                otherwise it will be disabled. Optional, True by default.
            - checked (bool): If True, the plugin will be checked in the UI,
                otherwise it will be unchecked. Optional, True by default.
        """
        if item.type == "unreal.asset":
            return {
                "accepted": True,
                "enabled": True,
                "checked": True
            }
            
        return {
            "accepted": False,
            "enabled": False,
            "checked": False
        }

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish.
        """
        asset_type = settings["Asset Type"]
        if item.properties["asset_type"] != asset_type:
            self.logger.warning(
                "Asset type mismatch. Expected %s, got %s" % 
                (asset_type, item.properties["asset_type"])
            )
            return False
            
        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        # Get the export path
        export_template = self.get_template_by_name(settings["Export Path Template"])
        export_path = export_template.apply_fields(item.properties)
        
        # Export the asset
        asset = item.properties["unreal_asset"]
        if settings["Asset Type"] == "StaticMesh":
            self._export_static_mesh(asset, export_path)
        elif settings["Asset Type"] == "SkeletalMesh":
            self._export_skeletal_mesh(asset, export_path)
            
        return True

    def _export_static_mesh(self, asset, export_path):
        """
        Export a static mesh asset.
        """
        # Implement Unreal Engine specific export logic here
        pass

    def _export_skeletal_mesh(self, asset, export_path):
        """
        Export a skeletal mesh asset.
        """
        # Implement Unreal Engine specific export logic here
        pass
