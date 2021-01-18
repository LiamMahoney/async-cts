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
            # file artifact sent w/ file
            artifact_payload, file_payload = await self.parse_multi_part_CTS_request(request)
            
        #TODO: search data base for given type / value combination before submitting new search

        resp = await self.searcher(
                artifact_payload.get('type'), 
                artifact_payload.get('value'),
                file_payload=file_payload if file_payload else None
            )

        if (file_payload):
            # deleting temp file from server
            os.unlink(file_payload.get('path'))

        return web.json_response(resp)

    async def queryCapabilitiesHandler(self, request):
        # TODO: read config to determine if file uploads are enabled
        supported = await self.file_uploads_supported()
        return web.Response(text=f'Recieved queryCapabilitiesHandler request')

    async def parse_multi_part_CTS_request(self, request):
        """
        Parses the multi-part CTS request into the artifact information and
        file information.

        :param aiohttp.web_request.Request request: the incomming request from
        Resilient
        :returns array index 0 describes the artifact, index 1 describes the
        file
        """

        #TODO: check if file uploads are allowed in config before parsing the file
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
        #TODO: size should probably be limited in config
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

        return file_payload

    async def file_uploads_supported(self):
        """
        :returns boolean True if file uploads are suppored, False if they are
        not
        """
        raise Exception("NOT IMPLEMENTED YET")