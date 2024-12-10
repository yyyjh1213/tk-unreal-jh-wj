"""
Hook for publishing Unreal Engine assets.
"""
import sgtk
import os
import unreal
from ...common.base_publisher import BasePublisher

class UnrealAssetPublisher(BasePublisher):
    @property
    def publish_file_type(self):
        return "Unreal Asset"
        
    def _do_publish(self, settings, item, publish_path):
        """
        Save and publish the Unreal asset.
        """
        try:
            # Get the asset
            asset_path = item.properties.get("asset_path")
            if not asset_path:
                self.logger.error("No asset path found in item properties")
                return False
                
            asset = unreal.load_object(None, asset_path)
            if not asset:
                self.logger.error(f"Failed to load asset: {asset_path}")
                return False
                
            # Save the asset
            unreal.EditorAssetLibrary.save_loaded_asset(asset)
            
            # Copy to publish location if needed
            if publish_path != asset_path:
                unreal.EditorAssetLibrary.duplicate_asset(
                    asset_path,
                    publish_path
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to publish asset: {str(e)}")
            return False
