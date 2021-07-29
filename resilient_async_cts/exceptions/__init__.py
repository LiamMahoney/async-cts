class InvalidSearcherReturn(Exception):
    
    def __init__(self, message):
        super().__init__(self, message)

class FileExceededMaxSize(Exception):
    
    def __init__(self):
        super().__init__(self, "File exceeded max upload size")

class UnsupportedArtifactType(Exception):

    def __init__(self):
        super().__init__(self, "Unsupported artifact type")