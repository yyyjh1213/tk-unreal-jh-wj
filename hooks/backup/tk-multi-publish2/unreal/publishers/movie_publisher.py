"""
Hook for publishing movies from Unreal Engine.
"""
import os
import shutil
from ...common.base_publisher import BasePublisher

class MoviePublisher(BasePublisher):
    @property
    def publish_file_type(self):
        return "Movie"
        
    def _do_publish(self, settings, item, publish_path):
        """
        Copy the movie file to the publish location.
        """
        try:
            # Get source path
            source_path = item.properties.get("movie_path")
            if not source_path:
                self.logger.error("No movie path found in item properties")
                return False
                
            # Copy file
            shutil.copy2(source_path, publish_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to publish movie: {str(e)}")
            return False
