# Path: ./sources/syntrillo/api_healthie/tags.py
import json
import requests
from typing import Tuple

from syntrillo.api_healthie.auth import HealthieAuth

class HealthieTags():
    """
    A class handling tags


    """

    log = {
        'success': True,
        'logs': []
    }


    def __init__(self):
        self.auth = HealthieAuth()
        self._get_list_of_tags_and_users()


    def _get_list_of_tags_and_users(
        self,
        ) -> Tuple[dict, dict]:
        """
        Lit all tags

        https://docs.gethealthie.com/docs/#list-all-tags


        Returns:
            dict: returns list of folders based on the specified criteria.
        """
        # Set up the GraphQL query to list custom module forms
        query = '''
        query tags {
            tags {
                id
                name
                org_members_count
                tagged_users {
                    id
                    name
                }
            }
        }
        '''

        # Set up the GraphQL variables (if needed)
        variables = { }

        # Make the GraphQL query request using the send_query method inherited from HealthieAPI
        response, log = self.auth.send_query(query, variables)

        if log['success'] and response is not None and response['tags'] is not None:
            self._tags = response['tags']
        else:
            self.log['success'] = False
            self.log['logs'].append({
                'message' : 'Error while fetching tags',
                'log' : log
            })
            self._tags = None

    def get_tags(self):
        """
        Get tags and their users

        https://docs.gethealthie.com/schema/tag.doc

            tags {
                id
                name
                org_members_count
                tagged_users {
                    id
                    name
                }
            }

        Returns:
            dict: tags and their users
        """
        return self._tags

    def get_tag_ids_from_tag_name(
        self,
        tag_name: str,
        ) -> list[str]:
        """
        Get tag id from tag name

        Args:
            tag_name (str): tag_name

        Returns:
            str: tag_id
        """
        ids = []
        for tag in self._tags:
            if tag['name'] == tag_name:
                ids.append(tag['id'])
        return ids

    def get_user_ids_by_tag_name(
        self,
        tag_name: str,
        ) -> list[str]:
        """
        Get user ids by tag name

        Args:
            tag_name (str): tag_name

        Returns:
            list[str]: user_ids
        """
        user_ids = []
        for tag in self._tags:
            if tag['name'] == tag_name:
                for user in tag['tagged_users']:
                    user_ids.append(user['id'])
        return user_ids


if __name__ == '__main__':
    tags = HealthieTags()
    print(json.dumps(tags.get_tags(), indent=4, default=str))

    # get tag id of 'VCN' tag name
    tag_ids = tags.get_tag_ids_from_tag_name('VCN')
    print(tag_ids)

    # get users having the 'VCN' tag
    user_ids = tags.get_user_ids_by_tag_name('VCN')
    print(user_ids)





