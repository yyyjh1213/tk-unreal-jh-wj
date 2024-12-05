# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

import os
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class PublishPostProcessor(HookBaseClass):
    """
    Hook that runs after all publish plugins have completed.
    """

    def post_publish(self, work_template, primary_publish_path, sg_task, comment, thumbnail_path, parent_sg_entity, sg_task_step, additional_publish_fields):
        """
        Execute post publish operations.

        :param work_template: The primary work template
        :param primary_publish_path: Path to the primary published file
        :param sg_task: Shotgun task dictionary
        :param comment: Publish comment
        :param thumbnail_path: Path to the publish thumbnail
        :param parent_sg_entity: Parent entity dictionary
        :param sg_task_step: Shotgun task step dictionary
        :param additional_publish_fields: Additional fields to include in the publish
        """
        
        # get the current engine
        engine = sgtk.platform.current_engine()
        
        if engine.name == "tk-unreal":
            # if we're in Unreal, do any Unreal-specific post processing
            self._post_process_unreal(primary_publish_path, parent_sg_entity)
        elif engine.name == "tk-maya":
            # if we're in Maya, do any Maya-specific post processing
            self._post_process_maya(primary_publish_path, parent_sg_entity)
            
    def _post_process_unreal(self, publish_path, parent_entity):
        """
        Do any post-processing specific to Unreal Engine publishes.
        
        :param publish_path: Path to the published file
        :param parent_entity: Parent entity dictionary
        """
        # Add any Unreal-specific post processing here
        pass
        
    def _post_process_maya(self, publish_path, parent_entity):
        """
        Do any post-processing specific to Maya publishes.
        
        :param publish_path: Path to the published file
        :param parent_entity: Parent entity dictionary
        """
        # Add any Maya-specific post processing here
        pass
