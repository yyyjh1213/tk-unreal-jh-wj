"""
Hook for performing operations with maya.
"""
import maya.cmds as cmds
import maya.mel as mel
import os
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class SceneOperation(HookBaseClass):
    """
    Hook called to perform an operation with the
    current scene
    """

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

        :param file_version:    The version/revision of the file to be opened.  If this is 'None'
                              then the latest version should be opened.

        :param read_only:       Specifies if the file should be opened read-only or not

        :returns:              Depends on operation:
                              'current_path' - Return the current scene
                                             file path as a String
                              'reset'        - True if scene was reset to an empty
                                             state, otherwise False
                              all others     - None
        """
        if operation == "current_path":
            return cmds.file(query=True, sceneName=True)
        elif operation == "open":
            # make sure the folder exists
            folder = os.path.dirname(file_path)
            self.parent.ensure_folder_exists(folder)

            cmds.file(file_path, open=True, force=True)
        elif operation == "save":
            # make sure the folder exists
            folder = os.path.dirname(file_path)
            self.parent.ensure_folder_exists(folder)

            cmds.file(rename=file_path)
            cmds.file(save=True, force=True)
        elif operation == "save_as":
            # make sure the folder exists
            folder = os.path.dirname(file_path)
            self.parent.ensure_folder_exists(folder)

            cmds.file(rename=file_path)
            cmds.file(save=True, force=True)
        elif operation == "reset":
            """
            Reset the scene to an empty state
            """
            while cmds.file(query=True, modified=True):
                # Scene has been modified:
                res = cmds.confirmDialog(title="Save your scene?",
                                       message="Your scene has unsaved changes. Save before proceeding?",
                                       button=["Save", "Don't Save", "Cancel"],
                                       defaultButton="Save",
                                       cancelButton="Cancel",
                                       dismissString="Cancel")

                if res == "Save":
                    scene_name = cmds.file(query=True, sceneName=True)
                    if not scene_name:
                        cmds.SaveSceneAs()
                    else:
                        cmds.file(save=True)
                elif res == "Cancel":
                    return False
                else:
                    break

            # do new file:
            cmds.file(newFile=True, force=True)
            return True
        elif operation == "clean":
            # make sure the folder exists
            folder = os.path.dirname(file_path)
            self.parent.ensure_folder_exists(folder)

            # Save current scene with clean settings
            cmds.file(rename=file_path)
            cmds.file(save=True, force=True, type="mayaAscii")
