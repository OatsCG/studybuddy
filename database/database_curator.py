import sqlite3
from typing import Any

class AssignmentsDatabase:
    '''
    Represents an Assignments database parser and writer.

    db_name:
        The location of this database

    '''
    db_name: str
    _db_connection: sqlite3.Connection
    _db_cursor: sqlite3.Cursor

    def __init__(self, filename: str) -> None:
        self.db_name = filename
        self._SETUP_completely_erase_database()
        self._SETUP_start_connection()
        self._SETUP_add_table_Users()

    
    def _SETUP_completely_erase_database(self) -> None:
        '''
        CAREFUL! Completely erases all users and records; creates new file at self.db_name
        '''
        open(self.db_name, 'w').close()
    
    def _SETUP_start_connection(self) -> None:
        '''
        Starts sqlite3 connection to database
        '''
        self._db_connection = sqlite3.connect(self.db_name)
        self._db_cursor = self._db_connection.cursor()

    def _SETUP_add_table_Users(self) -> None:
        self._db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users(
                discordID TEXT,
                timezone TEXT
            )
        ''')
        self._db_connection.commit()
    
    def add_new_user(self, discordID: str, timezone: str) -> None:
        '''
        Creates new user and new assignments table
        '''
        self._db_cursor.execute(f'''
            INSERT INTO Users(discordID, timezone)
            VALUES
            (?, ?)
        ''', (self._format_discordID(discordID), timezone))
        
        self._db_cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self._format_discordID(discordID)}(
                assignmentIndex INT,
                name TEXT,
                startdate INT,
                durationSeconds INT
            )
        ''')
        self._db_connection.commit()
    
    def add_new_assignment(self, discordID: int, name: str, startdate: int, durationSeconds: int) -> None:
        '''
        Creates a new assignment for the user at discordID
        '''
        self._db_cursor.execute(f'''
            INSERT INTO {self._format_discordID(discordID)}(index, name, startdate, durationSeconds)
            VALUES
            (?, ?, ?, ?)
        ''', (name, startdate, durationSeconds))
        self._db_connection.commit()

    def _format_discordID(self, discordID: int) -> str:
        '''
        Prepends 'a' to the discordID for compatibility with sqlite3
        '''
        return ('a' + str(discordID))
    
    def does_user_exist() -> bool:
        '''
        Returns if a user exists
        '''
        raise NotImplementedError
    
    def does_assignment_exist(self, assignmentIndex: int) -> bool:
        '''
        Returns the assignment at id
        '''
        raise NotImplementedError
    
    def get_number_assignments(self, discordID: int) -> int:
        '''
        returns the number of assignments for a user
        '''
        self._db_cursor.execute(f"SELECT COUNT(*) FROM {self._format_discordID(discordID)}")
        result = self._db_cursor.fetchone()
        return(result)
    
    def get_user(self, discordID: int) -> dict[str: Any]:
        '''
        Returns the user's data

        {"discordID": int, "timezone": str}
        '''
        raise NotImplementedError

    def get_user_assignments(self, discordID: int) -> list[dict[str, Any]]:
        '''
        Returns an unsorted list of the user's assignments

        [{"index": int, "name": str, "startdate": int, "durationSeconds": int}, ...]
        '''
        raise NotImplementedError
    
    def edit_user_timezone():
        raise NotImplementedError

    def remove_assignment():
        raise NotImplementedError



if __name__ == "__main__":
    # DATABASE TESTING
    database = AssignmentsDatabase("/Users/Charlie/Desktop/calbot/assignments.db")
    database.add_new_user("123", "EST")