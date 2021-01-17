import asyncio
import asyncpg

class CTSHub():

    def __init__(self, username, password, database, host):
        self.conn = await asyncpg.connect(user=username, password=password, database=database, host=host)

    async def closeConnectionDB(self):
        """
        Closes the connetion to the database.
        """
        await self.conn.close()

    async def searchForActiveSearch(self, artifactType, artifactValue):
        """
        Determines if the CTS is already looking up the given artifact type and value
        combination. If it is, then no need to launch a new search on the combination.

        :param <string> artifactType: the type of the artifact
        :param <string> artifactValue: value of the artifact
        """

    return None

    async def startSearch(self, artifactType, artifactValue):
        """
        Starts a new search on the artifact type and value combination.
        Generates a UUID and then hands execution off to the user-defined 
        search functionality.

        :param <string> artifactType: the type of the artifact
        :param <string> artifactValue: the value of the artifact
        """