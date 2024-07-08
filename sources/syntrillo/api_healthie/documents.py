# Path: ./sources/syntrillo/api_healthie/documents.py

import json
from typing import Tuple

from syntrillo.api_healthie.auth import HealthieAuth

class HealthieDocuments():
    """
    A class handling documents and folders related operations.

    Notes folders and documents can be 'private' or 'viewable (aka visible on the GUI)' by different users.
       - viewable_user_id
       - private_user_id
       - consolidated_user_id : ???


    """

    def __init__(self):
        self.auth = HealthieAuth()


    def list_folders(
        self,
        healthie_user_id: str,
        is_private_to_user: bool = False,
        is_viewable_to_user: bool = False,
        ) -> Tuple[dict, dict]:
        """
        List folders based on the specified criteria using the Healthie API.
        See :
           - https://docs.gethealthie.com/schema/folder.doc
           - https://docs.gethealthie.com/docs/#listing-documents

        Query (for reference):
            folders(
                client_id: String,
                consolidated_user_id: String,
                document_to_move_id: ID,
                filter: String,
                folder_id: String,
                folder_to_move_id: ID,
                for_template_use: Boolean,
                keywords: String,
                private_user_id: String,
                provider_id: ID,
                should_paginate: Boolean,
                order_by: FolderOrderKeys,
                viewable_user_id: String
            ): [Folder!]

        Parameters:
            healthie_user_id (str): The Healthie user ID.
            is_private_to_user (bool): Whether the folder is private to the user.
            is_viewable_to_user (bool): Whether the folder is viewable to the user.

        Returns:
            dict: returns list of folders based on the specified criteria.
        """
        # Set up the GraphQL query to list custom module forms
        query = '''
            query folders (
                $client_id : String,
                $viewable_user_id : String,
                $consolidated_user_id : String,
                $private_user_id : String
                ) {
                folders (
                    client_id: $client_id,
                    viewable_user_id : $viewable_user_id,
                    consolidated_user_id: $consolidated_user_id,
                    private_user_id: $private_user_id
                ) {
                    id,
                    name
                }
                }
        '''

        # Set up the variables for the GraphQL query

        viewable_user_id = None
        private_user_id = None
        consolidated_user_id = None
        if is_private_to_user:
            private_user_id = healthie_user_id
        elif is_viewable_to_user:
            viewable_user_id = healthie_user_id
        else:
            consolidated_user_id = healthie_user_id

        variables = {
            'consolidated_user_id': consolidated_user_id,
            'viewable_user_id': viewable_user_id,
            'private_user_id': private_user_id,
        }

        # Make the GraphQL query request using the send_query method inherited from HealthieAPI
        response, log = self.auth.send_query(query, variables)

        return response, log

    def get_folder_id_by_name(
        self,
        healthie_user_id: str,
        folder_name: str,
        is_private_to_user: bool = False,
        is_viewable_to_user: bool = False,
    ) -> str:
        """
        Get the folder ID by name based on the specified criteria using the Healthie API.

        Args:
            healthie_user_id (str): The Healthie user ID.
            folder_name (str): The name of the folder.
            is_private_to_user (bool): Whether the folder is private to the user.
            is_viewable_to_user (bool): Whether the folder is viewable to the user.

        Returns:
            str: The folder ID.


        """
        # Get the list of folders based on the specified criteria
        folders, _ = self.list_folders(
            healthie_user_id=healthie_user_id,
            is_private_to_user=is_private_to_user,
            is_viewable_to_user=is_viewable_to_user
        )

        # Find the folder ID by name
        folder_id = None
        for folder in folders['folders']:
            if folder['name'] == folder_name:
                folder_id = folder['id']
                break

        return folder_id


    def list_documents(
        self,
        healthie_user_id: str,
        is_private_to_user: bool = False,
        is_viewable_to_user: bool = False,
        folder_id: str = None,
    )-> Tuple[dict, dict]:
        """
        List documents based on the specified criteria using the Healthie API.

        Query (for reference):
            query documents(
            $offset: Int,
            $keywords: String,
            $folder_id: String,
            $file_type: String,
            $private_user_id: String,
            $viewable_user_id: String,
            $consolidated_user_id: String,
            $filter: String,
            $should_paginate: Boolean,
            $for_template_use: Boolean,
            $provider_id: ID
            ) {
            documents(
                offset: $offset,
                keywords: $keywords,
                folder_id: $folder_id,
                file_type: $file_type,
                private_user_id: $private_user_id,
                viewable_user_id: $viewable_user_id,
                consolidated_user_id: $consolidated_user_id,
                filter: $filter,
                should_paginate: $should_paginate,
                for_template_use: $for_template_use,
                provider_id: $provider_id
            ) {
                id
                display_name
                file_content_type
                opens {
                id
                }
                owner {
                id
                email
                }
                users {
                id
                email
                }
            }
            }



        """

        # Set up the GraphQL query to list custom module forms
        query = '''
            query documents (
                $offset: Int,
                $keywords: String,
                $folder_id: String,
                $file_type: String,
                $private_user_id: String,
                $viewable_user_id: String,
                $consolidated_user_id: String,
                $filter: String,
                $should_paginate: Boolean,
                $for_template_use: Boolean,
                $provider_id: ID
                ) {
                documents(
                    offset: $offset,
                    keywords: $keywords,
                    folder_id: $folder_id,
                    file_type: $file_type,
                    private_user_id: $private_user_id,
                    viewable_user_id: $viewable_user_id,
                    consolidated_user_id: $consolidated_user_id,
                    filter: $filter,
                    should_paginate: $should_paginate,
                    for_template_use: $for_template_use,
                    provider_id: $provider_id
                ) {
                    id
                    display_name
                    file_content_type
                }
                }
        '''

        # Set up the variables for the GraphQL query

        viewable_user_id = None
        private_user_id = None
        consolidated_user_id = None

        if is_private_to_user:
            private_user_id = healthie_user_id
        if is_viewable_to_user:
            viewable_user_id = healthie_user_id
        if not is_private_to_user and not is_viewable_to_user:
            consolidated_user_id = healthie_user_id

        variables = {
            'consolidated_user_id': consolidated_user_id,
            'viewable_user_id': viewable_user_id,
            'private_user_id': private_user_id,
            'folder_id': folder_id,
        }

        # Make the GraphQL query request using the send_query method inherited from HealthieAPI
        response, log = self.auth.send_query(query, variables)

        return response, log


if __name__ == '__main__':
    # Test the HealthieDocuments class
    healthie_documents = HealthieDocuments()

    # ---
    # Test the list_folders method
    response, _ = healthie_documents.list_folders(
        healthie_user_id='1035117',
        is_private_to_user=True
        )

    print(response)

    # ---
    # Test the get_folder_id_by_name method
    folder_id = healthie_documents.get_folder_id_by_name(
        healthie_user_id='1035117',
        folder_name='discharge_documents',
        is_private_to_user=True
        )

    print(folder_id)

    # ---
    # Test the list_documents method
    documents, _ = healthie_documents.list_documents(
        healthie_user_id='1035117',
        is_private_to_user=True,
        folder_id=folder_id
        )

    print(json.dumps(documents, indent=4, default=str))




