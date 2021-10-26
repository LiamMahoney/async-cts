class ResponseDTO(dict):
    """
    A response payload from the CTS to IBM Security SOAR.
    """

    def __init__(self, id, retry_secs=None, hits=None):
        """
        :param string id: the ID of the search the request provided
        :param int retry_secs: the number of seconds IBM Security SOAR should 
        wait before sending another request about this search
        :param ArtifactHitDTO hits: the hit(s) found for the artifact
        """
        if (not id):
            raise ValueError("Missing required value id")

        # have to check for None instead of falsy values, empty hits are empty
        # lists
        if (retry_secs == None and hits == None):
            raise ValueError("Must supply either retry_secs or hits")

        response = {
            'id': id
        }

        if (retry_secs):
            response['retry_secs'] = retry_secs

        if (hits):
            response['hits'] = hits

        super().__init__(response)
