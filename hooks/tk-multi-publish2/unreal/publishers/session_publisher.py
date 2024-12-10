"""
Hook for publishing the current Unreal Engine session.
"""
import sgtk
from ...common.base_publisher import BasePublisher

class UnrealSessionPublisher(BasePublisher):
    @property
    def publish_file_type(self):
        return "Unreal Level"
        
    def _do_publish(self, settings, item, publish_path):
        """
        Save the current Unreal level.
        """
        try:
            # Get engine
            engine = self.parent.engine
            
            # Save current level
            engine.save_current_level(publish_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save level: {str(e)}")
            return False
