"""
Common utility functions for publish hooks.
"""
import os
import sgtk

def get_icon_path(hook_instance, icon_name):
    """
    Return the full path to the given icon.
    """
    return os.path.join(
        hook_instance.disk_location,
        os.pardir,
        "icons",
        f"{icon_name}.png"
    )

def ensure_folder_exists(path):
    """
    Ensure the folder exists for the given path.
    """
    folder = os.path.dirname(path)
    if not os.path.exists(folder):
        os.makedirs(folder)

def get_template_from_settings(settings, publisher, template_key="Publish Template"):
    """
    Get and validate template from settings.
    """
    template_setting = settings.get(template_key)
    if not template_setting:
        raise ValueError(f"Missing '{template_key}' setting")
        
    template_name = template_setting.value
    template = publisher.sgtk.templates.get(template_name)
    
    if not template:
        raise ValueError(f"Could not find template '{template_name}' in config")
        
    return template

def get_publish_data(publisher, item, path, file_type=None):
    """
    Get common publish data dictionary.
    """
    return {
        "tk": publisher.sgtk,
        "context": item.context,
        "comment": item.description,
        "path": path,
        "name": item.name,
        "version_number": item.properties.get("version_number", 1),
        "thumbnail_path": item.get_thumbnail_as_path(),
        "published_file_type": file_type
    }
