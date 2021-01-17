import asyncio, tempfile, os
from aiohttp import web, MultipartReader

class AsyncCTS():
    
    def __init__(self, searcher):
        # TODO: THESE SHOULD BE READ IN FROM CONFIG FILE
        self.username = "userame"
        self.password = "password"
        self.database = "test"
        self.host = "0.0.0.0"
        ################################################

        self.searcher = searcher

    async def getServer(self):
        app = web.Application()

        app.add_routes([
            web.get('/{id}', self.retrieveArtifactResultHandler),
            web.post('/', self.scanArtifactHandler),
            web.options('/', self.queryCapabilitiesHandler)
        ])

        return app

    async def retrieveArtifactResultHandler(self, request):
        id = request.match_info.get('id', 'Anonymous')
        return web.Response(text=f'Recieved retrieveArtifactResultHandler request with id {id}')

    async def scanArtifactHandler(self, request):
        
        # will always be set - type / value combination of the artifact
        artifact_payload = None
        # only set for file artifacts - path to temp file and encoding
        file_payload = None

        if (request.content_type == 'application/json'):
            # non file artifact

            artifact_payload = await request.json()

        else:
            # file artifact sent

            #TODO: put into a separate function that takes in the request and place in a separate file
            # should throw OperationNotSupported exception if file is sent but config says no
            
            #TODO: check if file uploads are allowed in config before parsing the file

            reader = await request.multipart()
            
            # temporary file to write file contents to
            file_object = tempfile.NamedTemporaryFile('wb', delete=False)

            # first part of request contains typical artifact type / value
            # (value = file name in this case) json object
            artifact_part = await reader.next()
            artifact_payload = await artifact_part.json()

            # second part of request contains the file contents
            file_part = await reader.next()

            # reading parts / chunks of file and writing to temp file
            size = 0
            while True:
                # reading raw binary data
                chunk = await file_part.read_chunk()
                if (not chunk):
                    break
                size += len(chunk)
                file_object.write(chunk)
                file_object.flush()

            file_payload = {
                "path": file_object.name,
                "Content-Transfer-Encoding": file_part.headers.get("Content-Transfer-Encoding")
            }

            file_object.close()

        #TODO: search data base for given type / value combination before submitting new search

        resp = await self.searcher(
                artifact_payload.get('type'), 
                artifact_payload.get('value'),
                file_payload=file_payload if file_payload else None
            )

        if (file_payload):
            os.unlink(file_object.name)

        return web.json_response(resp)

    async def queryCapabilitiesHandler(self, request):
        # TODO: read config to determine if file uploads are enabled
        return web.Response(text=f'Recieved queryCapabilitiesHandler request')

    async def parseFileHandler(self, request):
        """
        Creates a temporary file that contians the contents of the file sent
        by Resilient.

        :param aiohttp.web_request.Request request: the incomming request from
        Resilient
        :returns dict 
        """