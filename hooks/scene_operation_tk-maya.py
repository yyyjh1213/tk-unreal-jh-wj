import os
import maya.cmds as cmds
import sgtk
from sgtk.platform.qt import QtGui

HookBaseClass = sgtk.get_hook_baseclass()

class SceneOperation(HookBaseClass):
    def execute(self, operation, file_path, context, parent_action, file_version, read_only, **kwargs):
        """
        Main hook entry point
        
        :param operation:       String
                               Scene operation to perform
        :param file_path:       String
                               File path to use if the operation
                               requires it (e.g. open)
        :param context:         Context
                               The context the file operation is being
                               performed in.
        :param parent_action:   This is the action that this scene operation is
                               being executed for.  This can be one of:
                               - open_file
                               - new_file
                               - save_file_as
                               - version_up
                               - clean_file
        """
        
        if operation == "save":
            # Maya can choose the appropriate file type automatically
            cmds.file(save=True, force=True)
        elif operation == "save_as":
            try:
                if parent_action == "clean_file":
                    # Clean up the scene before saving
                    # Add your clean-up operations here
                    # For example:
                    # - Delete unused nodes
                    # - Optimize scene
                    # - Export as FBX
                    
                    # Save the file using the clean template
                    clean_template = self.parent.get_template("template_clean")
                    if clean_template:
                        clean_path = clean_template.apply_fields(context.as_template_fields())
                        
                        # Ensure the directory exists
                        clean_dir = os.path.dirname(clean_path)
                        self.parent.ensure_folder_exists(clean_dir)
                        
                        # Save as FBX
                        cmds.file(clean_path, force=True, options="v=0;", typ="FBX export", pr=True, ea=True)
                        
                        # Show success message
                        QtGui.QMessageBox.information(None, 
                                                    "Save Completed", 
                                                    "Scene has been cleaned and saved to:\n%s" % clean_path)
                        return True
            except Exception as e:
                QtGui.QMessageBox.critical(None, 
                                         "Save Failed", 
                                         "Failed to save file:\n%s" % str(e))
                return False
        
        # Fall back to default implementation
        return super(SceneOperation, self).execute(operation, 
                                                 file_path, 
                                                 context, 
                                                 parent_action, 
                                                 file_version, 
                                                 read_only, 
                                                 **kwargs)
