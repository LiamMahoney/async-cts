import motor.motor_asyncio
import os
import datetime
from bson.objectid import ObjectId
from .config import config
from ..exceptions import BaseAsyncCTSError

class Mongo():
    """
    Contains all of the needed interactions with MongoDB for Resilient Async 
    CTS.
    """

    def __init__(self):
        #TODO: require mongo authentication
        client = motor.motor_asyncio.AsyncIOMotorClient(f"mongodb://{config['database'].get('host')}:{config['database'].get('port')}")

        self.db = client[f'{config["cts"].get("id")}']

        self.active_searches_collection_name = f'{config["cts"].get("id")}_active_searches'
        self.results_collection_name = f'{config["cts"].get("id")}_results'

    async def add_ttl_to_results_collection(self):
        """
        Adds a TTL (time to live) index on the results colleciton. Documents 
        will be removed from the collection after the amount of seconds 
        specified. Prevents stale hit data from being sent back to Resilient.
        The TTL number of seconds should be specified in the app's config.
        """
        await self.db[self.results_collection_name].create_index('date', expireAfterSeconds=config['cts'].getint('hit_ttl'))

    async def add_active_search(self, artifact_type, artifact_value):
        """
        Adds an entry to the 'active search' collection. An entry to the active
        search collection should be added before the search is started.

        :param string artifact_type: the type of the artifact to add
        :param string artifact_value: the value of the artifact to add
        :returns string the ID of the document added to the active search 
        collection
        :raises InsertException when there's an error inserting a document into
        the collection
        """
        document = {
            'artifact_type': artifact_type,
            'artifact_value': artifact_value
        }

        result = await self.db[self.active_searches_collection_name].insert_one(document)
        
        if (result.acknowledged):
            return str(result.inserted_id)
        else:
            raise InsertException(f'failed to insert a document into the active searches collection for artifact type {artifact_type} and value {artifact_value}')

    async def search_for_active_search(self, search_id=None, artifact_type=None, artifact_value=None):
        """
        Searches for an entry in the 'active search' collection with the given 
        search_id or the given artifact_value / artifact_type combination. 

        :param string search_id: the ID of the search to look for
        :param string artifact_type: the type of the artifact to look for. If
        supplied artifact_value must also be supplied
        :param string artifact_value: the value of the artifact to look for. If
        supplied artifact_type must also be supplied
        """
        if (search_id):
            document = await self.db[self.active_searches_collection_name].find_one(
                    {'_id': ObjectId(search_id)}
                )
        elif(artifact_type and artifact_value):
            document = await self.db[self.active_searches_collection_name].find_one(
                { 
                    '$and': [
                        {
                            'artifact_value': {
                                '$eq': artifact_value
                            }
                        }, 
                        {
                            'artifact_type': {
                                '$eq': artifact_type
                            }
                        }
                    ]
                }
            )
        else:
            raise ValueError('need to supply either search_id or artifact_type and artifact_value')

        return document

    async def find_all_active_searches(self):
        """
        Searches for any entries in the active_searches table.

        :returns MotorCursor that can be iterated over to get every document in
        the active_searches collection
        """
        # all documents in active_searches collection
        return self.db[self.active_searches_collection_name].find()

    async def remove_active_search(self, search_id):
        """
        Removes an entry from the active search collection. Should be called
        once a search has been complete to signal the search is no longer 
        running.

        :param string search_id: the ID of teh search to remove
        :returns Boolean True if the delete worked properly
        :raises DeletedMultipleActiveSearches if multiple entries are deleted
        :raises ActiveSearchNotFound if no entries are deleted
        """
        result = await self.db[self.active_searches_collection_name].delete_many({'_id': ObjectId(search_id)})

        if (result.deleted_count == 1):
            return True
        elif (result.deleted_count > 1):
            raise DeletedMultipleActiveSearches(search_id)
        elif (result.deleted_count < 1):
            raise ActiveSearchNotFound(search_id)

    async def search_for_results(self, search_id=None, artifact_type=None, artifact_value=None):
        """
        Searches for an entry in the 'results' collection with the given 
        search_id or the given artifact_value / artifact_type combination. 

        :param string search_id: the ID of the active search to look for
        :param string artifact_type: the type of the artifact to look for. If
        supplied artifact_value must also be supplied
        :param string artifact_value: the value of the artifact to look for. If
        supplied artifact_type must also be supplied
        """
        if (search_id):
            # not casting search_id to ObjectId because the ID came from the
            # active searches collection and is stored in the results table as
            # a string instead of an ObjectId
            document = await self.db[self.results_collection_name].find_one(
                    {'search_id': search_id}
                )
        elif(artifact_type and artifact_value):
            document = await self.db[self.results_collection_name].find_one(
                { 
                    '$and': [
                        {
                            'artifact_value': {
                                '$eq': artifact_value
                            }
                        }, 
                        {
                            'artifact_type': {
                                '$eq': artifact_type
                            }
                        }
                    ]
                }
            )
        else:
            raise ValueError('need to supply either search_id or artifact_type and artifact_value')

        return document

    async def store_search_results(self, search_id, artifact_type, artifact_value, hit):
        """
        Stores the results of a search.

        :param string search_id: the id of the active search
        :param string artifact_type: the type of artifact the search was
        performed on
        :param string artifact_value: the value the search was performed on
        :param ArtifactHitDTO hit: the hit generated from the search
        """
        document = {
            'search_id': search_id,
            'artifact_type': artifact_type,
            'artifact_value': artifact_value,
            'hit': hit,
            'date': datetime.datetime.now()
        }

        result = await self.db[self.results_collection_name].insert_one(document)

        if (result.acknowledged):
            return str(result.inserted_id)
        else:
            raise InsertException(f'failed to insert a document into the results collection.\nartifact type: {artifact_type}\nartifact value: {artifact_value}\nhit: {hit}')

class InsertException(BaseAsyncCTSError):

    def __init__(self, message):
        super().__init__(self, message)

class DeletedMultipleActiveSearches(BaseAsyncCTSError):

    def __init__(self, search_id):
        super().__init__(self, f'search_id: {search_id}')

class ActiveSearchNotFound(BaseAsyncCTSError):

    def __init__(self, search_id=None, artifact_type=None, artifact_value=None):
        message = ""
        
        if (search_id):
            message = f"Couldn't find an active search with id {search_id}"
        elif (artifact_type and artifact_value):
            message = f"Couldn't find an active search with type {artifact_type} and value {artifact_value}"
        
        super().__init__(self, message)