class BaseAsyncCTSError(Exception):

    pass

class InvalidSearcherReturn(BaseAsyncCTSError):
    
    def __init__(self, message):
        super().__init__(self, message)

class FileExceededMaxSize(BaseAsyncCTSError):
    
    def __init__(self):
        super().__init__(self, "File exceeded max upload size")

class UnsupportedArtifactType(BaseAsyncCTSError):

    def __init__(self):
        super().__init__(self, "Unsupported artifact type")
