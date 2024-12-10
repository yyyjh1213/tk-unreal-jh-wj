"""
Unreal collector for gathering publishable items.
"""
import sgtk
from ...common.base_collector import BaseCollector

class UnrealCollector(BaseCollector):
    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current Unreal session and creates publishable items.
        """
        engine = self.parent.engine
        
        # Create session item
        session_item = parent_item.create_item(
            "unreal.session",
            "Unreal Session",
            "Current Unreal Session"
        )
        
        try:
            # Get selected items
            selected_items = engine.get_selected_items()
            
            for item in selected_items:
                # Create publish item for each asset
                asset_item = parent_item.create_item(
                    "unreal.asset",
                    "Unreal Asset",
                    item.get_name()
                )
                
                # Set properties
                asset_item.properties["asset_type"] = item.get_type()
                asset_item.properties["content_path"] = item.get_path()
                
        except Exception as e:
            self.logger.error(f"Error processing items: {str(e)}")
            
        return session_item
