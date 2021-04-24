import asyncio
import tempfile
import os
import uuid
import json
from aiohttp import web, MultipartReader
from .util import Mongo
from .dto import ArtifactHitDTO, ResponseDTO
from .util import log
from .util import config

class CustomThreatService():
    """
    A class used to build Custom Threat Services for IBM Security SOAR. An 
    instance of this class must be passed a 'searcher' functoin that implements
    the 'search' of the CTS. The search can be looking up the artifact in an,
    API, querying for more information about th eartifact in a database or 
    file, or whatever is needed to be done to enrich an artifact.
    """

    async def initialize(self):
        """
        Runs everything that needs to happen in order for the CTS to run.
        1. checks that a connection to CTS hub can be made
        2. checks that a table for this CTS is created in CTS hub
        2a. if a table is not made, it creates the tables required
        3. initializes the webserver

        :returns aiohttp.web_app.Application the webserver for the CTS to run
        """
        log.info(f'Starting initialization')

        log.info(f'Testing connection to CTS Hub running on host {config["database"]["host"]}')

        try:
            mongo = Mongo()
            # deletes results after TTL so stale data isn't used
            await mongo.add_ttl_to_results_collection()
        except Exception as e:
            log.critical(f'Error connectiong to CTS Hub. Please make sure CTS Hub is running and the connection information is correct.')
            raise e

        log.info('Successfully connected to CTS Hub')
        
        # MotorCursor object
        active_search_cursor = await mongo.find_all_active_searches()

        async for search in active_search_cursor:
            # removing all of the active searches
            log.info(f'Removing search {str(search.get("_id"))} for {search.get("artifact_type")} {search.get("artifact_value")} from the active_searches table')
            await mongo.remove_active_search(str(search.get('_id')))

        log.info('Initialization complete')
        # returning webserver that the CTS will run
        return await self.getServer()

    async def getServer(self):
        """
        Creates the webserver that the CTS runs so Resilient can connect to it.
        Defines what actions should happen for each path that the server 
        accepts.

        :returns aiohttp.web_app.Application the webserver for the CTS to run
        """
        app = web.Application()

        # paths / methods the webserver listens to
        app.add_routes([
            web.get('/{id}', self.retrieveArtifactResultHandler),
            web.post('/', self.scanArtifactHandler),
            web.options('/', self.queryCapabilitiesHandler)
        ])

        return app

    async def retrieveArtifactResultHandler(self, request):
        """
        Checks if the search ID sent from Resilient is still in the active
        searches table. If it is assumed the search is still running. If it is
        not then it is assumed the search is done, and the results are
        retrieved and returned to Resilient.

        :returns web response that contains a ResponseDTO
        """
        id = request.match_info.get('id')
        log.info(f'GET {id}')

        mongo = Mongo()

        # determining if the search is still running or if the search has 
        # completed and it's results are stored
        if (await mongo.search_for_active_search(search_id=id) != None):
            # entry for ID in active searches, search is still running
            return web.json_response(
                ResponseDTO(id, retry_secs=config['cts']['retry_secs'])
            )
        else:
            # no entry for ID in active searches, search must be done
            results = await mongo.search_for_results(search_id=id)

            if (results):
                return web.json_response(
                    ResponseDTO(id, hits=json.loads(results.get('hit')))
                )
        
        log.critical(f"Unexpected state. Unable to find search id {id} in either active or results table")
        raise web.HTTPInternalServerError()

    async def scanArtifactHandler(self, request):
        """
        Recieves the artifact from Resilient request. Checks if there are any
        active searches with the given type / value combination. If an active
        search is found then that search ID is returned. If there isn't then 
        checks the results table for the type / value combination. If a result
        is found then the hit of that result is returned. If neither are found
        a new search is kicked off.

        :returns web response that contains a ResponseDTO object
        """
        
        # will always be set - type / value combination of the artifact
        artifact_payload = None
        # only set for file artifacts - path to temp file and encoding
        file_payload = None

        if (request.content_type == 'application/json'):
            # non file artifact
            artifact_payload = await request.json()

        else:
            if (await self.file_uploads_supported()):
                # file artifact sent w/ file
                artifact_payload, file_payload = await self.parse_multi_part_CTS_request(request)
            else:
                log.critical(f'Recieved a file but files are unsupported by this CTS.')
                raise web.HTTPUnsupportedMediaType()

        log.info(f'POST type: {artifact_payload.get("type")} value: {artifact_payload.get("value")}')

        mongo = Mongo()

        # searching for the type / value combination in both the active 
        # searches and search results dbs
        past_results, active_search = await asyncio.gather(
            mongo.search_for_results(artifact_type=artifact_payload.get('type'), artifact_value=artifact_payload.get('value')),
            mongo.search_for_active_search(artifact_type=artifact_payload.get('type'), artifact_value=artifact_payload.get('value'))
        )

        if (past_results == None and active_search == None):
            log.info(f"Submitting a new search for artifact {artifact_payload.get('type')} {artifact_payload.get('value')}")
            # no current searches or search results with the given type / value
            # launching a new search on the type / value
            response = await self.launch_new_search(mongo, artifact_payload, file_payload)

            return web.json_response(response)

        elif (active_search):
            log.info(f"Found an active saerch for artifact {artifact_payload.get('type')} {artifact_payload.get('value')}")
            # active search running for the given type / value combo, return
            # that search's ID
            return web.json_response(
                ResponseDTO(id, retry_secs=config['cts']['retry_secs'])
            )

        elif(past_results):
            log.info(f"Found a past result for artifact {artifact_payload.get('type')} {artifact_payload.get('value')}")
            # returning hit that was stored in db
            return web.json_response(
                ResponseDTO(id, hits=json.loads(past_results.get('hit')))
            )

        log.critical(f"Unexpected state. Either an existing hit or a new search should've prevented this from executing. Artifact type: {artifact_payload.get('type')}, artifact value: {artifact_payload.get('value')}")
        raise web.HTTPInternalServerError()

    async def queryCapabilitiesHandler(self, request):
        """
        Returns whether the CTS supports file uploads
        """
        supported = await self.file_uploads_supported()
        # returning ThreatServiceOptionsDTO
        return web.json_response(
            {
                'upload_file': supported
            }
        )

    async def parse_multi_part_CTS_request(self, request):
        """
        Parses the multi-part CTS request into the artifact information and
        file information.

        :param aiohttp.web_request.Request request: the incomming request from
        Resilient
        :returns array index 0 describes the artifact, index 1 describes the
        file
        """
        # CTS supports file uploads
        reader = await request.multipart()
    
        return await asyncio.gather(
            self.parse_multi_part_artifact(reader),
            self.parse_file(reader)
        )

    async def parse_multi_part_artifact(self, reader):
        """
        Parses the first part of the multi-part request which contains the
        artifact type / value combination.

        :param aiohttp.multipart.MultipartReader reader: multipart reader from
        the incomming request object
        Resilient
        :returns dict containing the artifact type / value, e.g.,
        {"type": "net.uri", "value": "https://liammahoney.dev"}
        """
        # first part of request contains typical artifact type / value
        # (value = file name in this case) json object
        artifact_part = await reader.next()
        return await artifact_part.json()

    async def parse_file(self, reader):
        """
        Creates a temporary file that contians the contents of the file sent
        by Resilient.

        :param aiohttp.multipart.MultipartReader reader: multipart reader from
        the incomming request object
        :returns dict describing the temp file created
        """
        # temporary file to write file contents to
        file_object = tempfile.NamedTemporaryFile('wb', delete=False)

        # second part of request contains the file contents
        file_part = await reader.next()

        # reading parts / chunks of file and writing to temp file
        size = 0
        while True:
            if (size < config['cts'].getint('max_upload_size')):
                # reading raw binary data
                chunk = await file_part.read_chunk()
                if (not chunk):
                    break
                size += len(chunk)
                file_object.write(chunk)
                file_object.flush()
            else:
                raise FileExceededMaxSize()

        #TODO: is Content-Transfer-Encoding header actually needed?
        file_payload = {
            "path": file_object.name,
            "Content-Transfer-Encoding": file_part.headers.get("Content-Transfer-Encoding")
        }

        file_object.close()

        return file_payload

    async def file_uploads_supported(self):
        """
        :returns boolean True if file uploads are suppored, False if they are
        not
        """
        return config['cts'].getboolean('upload_files')

    async def searcher(self):
        """
        This method should be overwritten.
        """
        raise Exception("THIS METHOD NEEDS TO BE OVERWRITTEN")

    async def launch_new_search(self, mongo, artifact_payload, file_payload=None):
        """
        Launches a new search on the artifact.

        :param dict artifact_payload: contains artifact type and value
        :param dict file_paylaod: contains the file path
        :param Mongo mongo: object that has methods to interact with the database

        :returns ResponseDTO that describes the search that was started
        """
        resp = asyncio.create_task(
            self.searcher(
                artifact_payload.get('type'), 
                artifact_payload.get('value'),
                file_payload=file_payload if file_payload else None
            )
        )

        # adding an entry to the active searches db
        search_id = await mongo.add_active_search(artifact_payload.get('type'), artifact_payload.get('value'))

        # when the search is done store it in the results table & remove 
        # the entry in the active searches table
        resp.add_done_callback(lambda future: self.search_complete_handler(future, search_id, artifact_payload.get("type"), artifact_payload.get("value"), file_payload, mongo))

        return ResponseDTO(search_id, retry_secs=config['cts']['retry_secs'])

    def search_complete_handler(self, future, search_id, artifact_type, artifact_value, file_payload, mongo):
        """
        Removes the search ID from the active searches DB and adds the results to
        the search results DB. If a file_payload is passed in then the temporary 
        file is removed from the server.

        :param future future: the results of the search (future object)
        :param string search_id: the active search ID to be removed
        :param string artifact_type: the type of the artifact
        :param string artifact_value: the value of the artifact
        :param dict file_payload: contains information about the file if one was
        sent from Resilient
        :param Mongo mongo: object that has methods to interact with the database
        """

        if (file_payload):
            # deleting temp file from server if Resilient sent a file
            os.unlink(file_payload.get('path'))

        # holds the exception raised in the future that is calling this function
        # if one occurred
        search_exception = future.exception()

        if (search_exception):
            # search raised exception, it is no longer searching / active
            asyncio.create_task(self.search_exception_handler(search_id, artifact_type, artifact_value, mongo))
            raise search_exception
        else:
            # schedule a task to remove the search from the active search data table 
            # and store the search results in the results table
            asyncio.create_task(self.search_complete_handler_helper(search_id, artifact_type, artifact_value, mongo, future.result()))

    async def search_complete_handler_helper(self, search_id, artifact_type, artifact_value, mongo, hit):
        """
        Stores the search results and of the search and then removes the search 
        from the active_searches table. Need to store the results first before
        removing the active search to eliminate a potential race case.

        :param string search_id: the active search ID to be removed
        :param string artifact_type: the type of the artifact
        :param string artifact_value: the value of the artifact
        :param Mongo mongo: object that has methods to interact with the database 
        :param HitDTO hit: the results of the search
        :raises InvalidSearcherReturn when the searcher function doesn't return an
        instance of ArtifactHitDTO
        """
        if (type(hit) == ArtifactHitDTO):
            log.info(f'Storing hit found in search id {search_id} for  {artifact_type} {artifact_value}')
            await mongo.store_search_results(search_id, artifact_type, artifact_value, json.dumps(hit))
            await mongo.remove_active_search(search_id)
        else:
            await mongo.remove_active_search(search_id)
            # this should stop execution of the CTS
            raise InvalidSearcherReturn(f'the return from the searcher function needs to be an instance of "ArtifactHitDTO"')

    async def search_exception_handler(self, search_id, artifact_type, artifact_value, mongo):
        """
        Removes the given search from the active searches table. Gets called when
        the searcher raises an exception. Stores an empty hit in teh results table
        to prevent an error when the retrieve artifact handler is called.

        :param string search_id the active search ID to be removed
        :param string artifact_type: the type of the artifact
        :param string artifact_value: the value of the artifact 
        :param Mongo mongo: object that has methods to interact with the database    
        """
        log.error(f'Exception raised during execution of the search function for search id {search_id}. Removing the search_id entry from the Active Searches table and inserting emtpy hit into the Results table')

        # not satisfied with storing an empty hit (implied not malicious) when an
        # error has occurred, but seems like the best bet at the moment
        await mongo.store_search_results(search_id, artifact_type, artifact_value, json.dumps(ArtifactHitDTO([])))
        await mongo.remove_active_search(search_id)

def InvalidSearcherReturn(Exception):
    
    def __init__(self, message):
        super().__init__(self, message)

def FileExceededMaxSize(Exception):
    
    def __init__(self):
        super().__init__(self, "File exceeded max upload size")