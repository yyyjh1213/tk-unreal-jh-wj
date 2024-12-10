"""
Collector for Unreal Engine that finds various publishable items in the current session.
"""
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class UnrealCollector(HookBaseClass):
    """
    Collector that operates on the current Unreal Engine session.
    """

    @property
    def item_filters(self):
        """
        List of item types that this collector is interested in.
        """
        return ["unreal.session", "unreal.asset"]

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session and creates publishable items for assets,
        levels, and other content.
        """
        self.logger.debug("Processing current Unreal session...")
        engine = self.parent.engine
        
        # Create an item representing the current Unreal session
        session_item = parent_item.create_item(
            "unreal.session",
            "Unreal Session",
            "Current Unreal Session"
        )
        
        try:
            # Get all selected actors/assets in the current level
            selected_items = engine.get_selected_items()
            self.logger.debug("Found %d selected items", len(selected_items))
            
            for item in selected_items:
                # Create a publish item for each selected asset
                asset_item = parent_item.create_item(
                    "unreal.asset",
                    "Unreal Asset",
                    item.get_name()
                )
                
                # Set additional properties
                asset_item.properties["asset_type"] = item.get_type()
                asset_item.properties["content_path"] = item.get_path()
                self.logger.debug("Created publish item for asset: %s", item.get_name())
                
        except Exception as e:
            self.logger.error("Error processing selected items: %s", str(e))
            
        return session_item
