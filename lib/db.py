import asyncio
import asyncpg
from functools import wraps

def handle_db_connection(func):
    """
    Decorator that creates a connection to the database, executes the function
    using the decorator and then closes the connection.
    NOTE: must be called from an instance of DB, or any class that has database
    information stored in the proper variables.
    TODO: move to separate file? maybe..
    """
    @wraps(func)
    async def inner(self, *args, **kwargs):
        conn = await asyncpg.connect(user=self.username, password=self.password, database=self.database, host=self.host)
        try:
            query_results = await func(self, conn, *args, **kwargs)
        finally:
            await conn.close()
        return query_results
    return inner

class DB():
    """
    Class that handles interacting with the data base to look for existing
    searches or results, add new searches or results and modify the data tables
    to keep their state in sync with what is needed for the application.
    """

    def __init__(self, username, password, database, host):
        #TODO: read these from config file, remove from constructor
        self.username = username
        self.password = password
        self.database = database
        self.host = host

    @handle_db_connection
    async def search_for_active_search(self, conn, artifact_type, artifact_value):
        """
        Determines if the CTS is already looking up the given artifact type and value
        combination. If it is, then no need to launch a new search on the combination.

        :param asyncpg.connection.Connection conn: connection to the database
        :param string artifact_type: the type of the artifact
        :param string artifact_value: value of the artifact
        """
        # TODO: read CTS id out of config and replace test_cts in query below with it
        row = await conn.fetch(f"SELECT * FROM test_cts_active_searches WHERE artifact_type = '{artifact_type}' AND artifact_value = '{artifact_value}';")

        return row

    @handle_db_connection
    async def search_for_results(self, conn, search_id=None, artifact_type=None, artifact_value=None):
        """
        Returns any results for the given artifact type / value combination or
        search id.
        NOTE: either artifact_type and artifact_value are required or just
        search_id.

        :param asyncpg.connection.Connection conn: connection to the database
        :param string artifact_type: the type of the artifact, if supplied
        artifact_value must also be supplied
        :param string artifact_value: value of the artifact, if supplied 
        artifact_type must also be supplied
        :returns 
        """

        if (not search_id and (not artifact_type or not artifact_value)):
            # no parameters provided
            raise Exception("search_id or artifact_typea and artifact_value are required parameters")

        results = None

        # TODO: read CTS id out of config and replace test_cts in query below with it
        if (search_id):
            # search_id supplied, retrieve results with it
            results = await conn.fetch(f"SELECT * FROM test_cts_results WHERE search_id = '{search_id}';")
        else:
            # artifact type / value supllied, retrieve results wtih it
            results = await conn.fetch(f"SELECT * FROM test_cts_results WHERE artifact_type = '{artifact_type}' AND artifact_value = '{artifact_value}';")

        return results

    @handle_db_connection
    async def remove_active_search(self, conn, search_id):
        """
        Deletes the entry from the active_searches table. Should occur when
        the search is complete.
        
        :param asyncpg.connection.Connection conn: connection to the database
        :param string search_id: the search ID to remove from the 
        active_searches table
        """

        results = await conn.execute("""
            DELETE FROM test_cts_active_searches
            WHERE search_id = $1
        """, search_id)

        return results
    
    @handle_db_connection
    async def add_active_search(self, conn, search_id, artifact_type, artifact_value):
        """
        Adds an entry to the 'active_searches' table. Should be called when a
        new search is started.

        :param asyncpg.connection.Connection conn: connection to the database
        :param string search_id: the search_id of the new search
        :param string artifact_type: the type of the artifact that is being 
        searched
        :param string artifact_value: the value of the artifact that is being
        searched
        
        """
        #TODO: get cts table name from config
        results = await conn.execute("""
            INSERT INTO test_cts_active_searches (id, search_id, artifact_type, artifact_value)
            VALUES (2, $1, $2, $3);
        """, str(search_id), artifact_type, artifact_value)

        return results