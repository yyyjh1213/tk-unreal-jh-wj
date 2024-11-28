"""
Hook called when performing a scene operation with Toolkit.
"""
import maya.cmds as cmds
import maya.mel as mel
import os
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class SceneOperation(HookBaseClass):
    """
    Hook called when performing a scene operation with Toolkit.
    """

    def execute(self, operation, file_path, context, parent_action, file_version, read_only, **kwargs):
        """
        Main hook entry point.
        
        :param operation:       String
                              Scene operation to perform
        :param file_path:      String
                              File path to use if the operation requires it
        :param context:        Context
                              The context the file operation is being performed in.
        :param parent_action:  This is the action that this scene operation is
                              being executed for.  This can be one of:
                              - open_file
                              - new_file
                              - save_file_as
                              - version_up
        :param file_version:   The version number of the file to be opened.  If
                              parent_action is 'version_up', this will be the
                              next version number.
        :param read_only:      Specifies if the file should be opened read-only or
                              not                        
        :returns:             Depends on operation:
                             'current_path' - Return the current scene file path as a String
                             all others     - Return None
        """
        # 모든 scene operation 코드를 주석 처리
        """
        if operation == "current_path":
            # return the current scene path
            return cmds.file(query=True, sceneName=True)
        elif operation == "open":
            # do new scene as Maya doesn't like opening 
            # the scene it currently has open!    
            cmds.file(new=True, force=True) 
            cmds.file(file_path, open=True)
        elif operation == "save":
            # save the current scene:
            cmds.file(save=True)
        elif operation == "save_as":
            # first rename the scene as file_path:
            cmds.file(rename=file_path)
            
            # Maya can choose the wrong file type so
            # we should set it here explicitly based
            # on the extension
            maya_file_type = None
            if file_path.lower().endswith(".ma"):
                maya_file_type = "mayaAscii"
            elif file_path.lower().endswith(".mb"):
                maya_file_type = "mayaBinary"
            
            # save the scene:
            if maya_file_type:
                cmds.file(save=True, type=maya_file_type)
            else:
                cmds.file(save=True)
        """
        pass
