"""
Hook for publishing movies from Unreal Engine to Shotgun.
"""
import os
from ..common.base_publisher import BasePublisher
from ..common import utils

class MoviePublisher(BasePublisher):
    """
    Plugin for publishing movies from Unreal Engine.
    """
    
    @property
    def accepted_item_types(self):
        return ["unreal.movie"]
    
    @property
    def publish_file_type(self):
        return "Movie"
    
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
        if item.type == "unreal.movie":
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
        # Make sure we have a valid movie file
        movie_path = item.properties.get("movie_path")
        if not movie_path or not os.path.exists(movie_path):
            self.logger.warning("Movie file does not exist: %s" % movie_path)
            return False
            
        return True

    def _do_publish(self, settings, item, publish_path):
        """
        Copy the movie file to the publish location.
        """
        # Copy the movie file to the publish location
        self._copy_movie_file(item.properties["movie_path"], publish_path)
    
    def _copy_movie_file(self, source_path, target_path):
        """
        Copy the movie file to the target location.
        """
        utils.ensure_folder_exists(target_path)
        
        # Use shutil to copy the file
        import shutil
        shutil.copy2(source_path, target_path)
