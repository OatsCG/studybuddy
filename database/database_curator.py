import sqlite3
from typing import Any

class tasksDatabase:
    '''
    Represents an tasks database parser and writer.

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
        CAREFUL! Completely erases all records; creates new file at self.db_name
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
    
    def add_new_user(self, discordID: int, timezone: str) -> None:
        '''
        Creates new user and new tasks table
        '''
        self._db_cursor.execute(f'''
            INSERT INTO Users(discordID, timezone)
            VALUES
            (?, ?)
        ''', (self._format_discordID(discordID), timezone))
        
        self._db_cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self._format_discordID(discordID)}(
                name TEXT,
                startdate INT,
                durationMinutes INT
            )
        ''')
        self._db_connection.commit()
    
    def add_new_task(self, discordID: int, name: str, startdate: int, durationMinutes: int) -> None:
        '''
        Creates a new task for the user at discordID
        '''
        self._db_cursor.execute(f'''
            INSERT INTO {self._format_discordID(discordID)}(name, startdate, durationMinutes)
            VALUES
            (?, ?, ?)
        ''', (name, startdate, durationMinutes))
        self._db_connection.commit()

    def _format_discordID(self, discordID: int) -> str:
        '''
        Prepends 'a' to the discordID for compatibility with sqlite3
        '''
        return ('a' + str(discordID))
    
    def _unformat_discordID(self, formatted_discordID: str) -> int:
        '''
        Removes the 'a' from the formatted discordID for frontend
        '''
        return int(formatted_discordID[1:])
    
    def does_user_exist() -> bool:
        '''
        Returns if a user exists
        '''
        raise NotImplementedError
    
    def does_task_exist(self, discordID: int, taskIndex: int) -> bool:
        '''
        Returns the task at taskIndex for discordID
        '''
        raise NotImplementedError
    
    def get_number_tasks(self, discordID: int) -> int:
        '''
        returns the number of tasks for a user
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

    def get_user_tasks(self, discordID: int) -> list[dict[str, Any]]:
        '''
        Returns a  list of the user's tasks sorted by startdate

        [{"taskIndex": int, "name": str, "startdate": int, "durationMinutes": int}, ...]
        '''
        raise NotImplementedError
    
    def edit_user_timezone():
        raise NotImplementedError

    def remove_tasks(self, discordID: int, taskIndex: int) -> None:
        '''
        Removes the task from discordID's tasks 
        '''
        raise NotImplementedError
    




if __name__ == "__main__":
    # DATABASE TESTING
    database = tasksDatabase("/Users/Charlie/Desktop/calbot/tasks.db")
    database.add_new_user(123, "EST")
    database.add_new_task(123, "CSC148 task 1", 123456, 0)
    database.add_new_user(5593, "GST")
    database.add_new_task(123, "CSC148 task 2", 888886, 0)
    database.add_new_task(5593, "MAT102 Exam", 111111, 120)