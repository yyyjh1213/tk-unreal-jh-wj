"""
Hook for publishing Unreal Engine assets to Shotgun.
"""
import sgtk
import os
import unreal
import stat
import glob
import time

HookBaseClass = sgtk.get_hook_baseclass()

class UnrealAssetPublisher(HookBaseClass):
    """
    Hook for publishing Unreal Engine assets to Shotgun.
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
        # Make sure we have a content path
        content_path = settings.get("Content Path")
        if not content_path:
            self.logger.warning("No content path specified in settings")
            return False
            
        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.
        """
        publisher = self.parent
        
        # Get the publish template from settings
        publish_template_setting = settings.get("Publish Template")
        if not publish_template_setting:
            raise ValueError(
                "Missing 'Publish Template' setting for the asset publisher."
            )
            
        # Get the template by name
        templates = publisher.sgtk.templates
        template = templates.get(publish_template_setting.value)
        if not template:
            raise ValueError(
                f"Could not find template '{publish_template_setting.value}' in the template config."
            )
        
        # Get fields from the current context
        fields = publisher.context.as_template_fields(template)
        
        # Update fields with item properties
        fields.update(item.properties)
        
        # Apply fields to template to get the publish path
        publish_path = template.apply_fields(fields)
        
        # Ensure the publish folder exists and has correct permissions
        self._ensure_folder_exists(publish_path)
        self._check_permissions(publish_path)
        
        # Get the asset path from item properties
        asset_path = item.properties.get("asset_path")
        if not asset_path:
            self.logger.error("No asset_path found in item properties")
            return False
            
        try:
            # Ensure the asset is writable and not locked
            if not self._ensure_file_writable(asset_path):
                self.logger.error(f"Failed to make asset writable: {asset_path}")
                return False

            # Save the asset using improved save package method
            if not self._safe_save_package(asset_path, publish_path):
                self.logger.error(f"Failed to save asset: {asset_path}")
                return False
            
            # Register the publish
            publish_data = {
                "tk": publisher.sgtk,
                "context": item.context,
                "comment": item.description,
                "path": publish_path,
                "name": item.name,
                "version_number": item.properties.get("version_number", 1),
                "thumbnail_path": item.get_thumbnail_as_path(),
                "published_file_type": settings.get("Asset Type", {}).get("value", "Asset")
            }
            
            # Register the publish using the base class' utility method
            super(UnrealAssetPublisher, self)._register_publish(**publish_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save asset: {str(e)}")
            return False

    def _ensure_folder_exists(self, path):
        """
        Ensure the folder exists for the given path.
        """
        folder = os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)

    def _check_permissions(self, path):
        """
        Check and set appropriate permissions for the file path.
        """
        try:
            # Ensure directory exists with write permissions
            directory = os.path.dirname(path)
            os.makedirs(directory, exist_ok=True)
            
            # If file exists, ensure it's writable
            if os.path.exists(path):
                current_mode = os.stat(path).st_mode
                os.chmod(path, current_mode | stat.S_IWRITE)
                
            return True
        except Exception as e:
            self.logger.error(f"Permission error: {str(e)}")
            return False

    def _ensure_file_writable(self, asset_path):
        """
        Ensure the asset file is writable and not locked.
        """
        try:
            if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
                # Check if asset is locked and force checkout if necessary
                if unreal.EditorAssetLibrary.is_asset_locked(asset_path):
                    unreal.EditorAssetLibrary.force_asset_checkout(asset_path)
                    
                # Wait briefly to ensure the checkout is complete
                time.sleep(0.5)
                
            return True
        except Exception as e:
            self.logger.error(f"Failed to make asset writable: {str(e)}")
            return False

    def _safe_save_package(self, asset_path, publish_path):
        """
        Safely save the asset package with improved error handling and temp file management.
        """
        try:
            # Get the asset
            asset = unreal.load_object(None, asset_path)
            if not asset:
                self.logger.error(f"Failed to load asset at path: {asset_path}")
                return False

            # Setup temp directory in project's Saved folder
            temp_dir = os.path.join(unreal.Paths.project_saved_dir(), "Temp")
            os.makedirs(temp_dir, exist_ok=True)

            # Clean up any existing temp files
            temp_pattern = os.path.join(temp_dir, "*.tmp")
            for temp_file in glob.glob(temp_pattern):
                try:
                    os.remove(temp_file)
                except:
                    pass

            # Save the asset with multiple retries
            max_retries = 3
            retry_delay = 1.0  # seconds
            
            for attempt in range(max_retries):
                try:
                    # Save the asset
                    unreal.EditorAssetLibrary.save_loaded_asset(asset)
                    
                    # If we get here, save was successful
                    return True
                except Exception as e:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Save attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        self.logger.error(f"All save attempts failed: {str(e)}")
                        return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to save package: {str(e)}")
            return False
