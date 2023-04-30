import sqlite3
from typing import Any, Union
from database.ics_parser import parse_ics

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

    
    def _SETUP_completely_erase_database(self) -> bool:
        '''
        CAREFUL! Completely erases all records; creates new file at self.db_name.

        Returns success.
        '''
        try:
            open(self.db_name, 'w').close()
            return True
        except:
            return False
    
    def _SETUP_start_connection(self) -> bool:
        '''
        Starts sqlite3 connection to database.

        Returns success.
        '''
        try:
            self._db_connection = sqlite3.connect(self.db_name)
            self._db_cursor = self._db_connection.cursor()
            return True
        except:
            return False

    def _SETUP_add_table_Users(self) -> None:
        self._db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users(
                discordID TEXT,
                timezone TEXT
            )
        ''')
        self._db_connection.commit()
    
    def add_new_user(self, discordID: int, timezone: str) -> bool:
        '''
        Creates new user and new tasks table.

        Returns success.
        '''
        try:
            self._db_cursor.execute(f'''
                INSERT INTO Users(discordID, timezone)
                VALUES
                (?, ?)
            ''', (self._format_discordID(discordID), timezone))
            
            self._db_cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self._format_discordID(discordID)}(
                    name TEXT,
                    startdate INT,
                    enddate INT
                )
            ''')
            self._db_connection.commit()
            return True
        except:
            return False
    
    def add_new_task(self, discordID: int, name: str, startdate: int, enddate: int) -> bool:
        '''
        Creates a new task for the user at discordID.

        Returns success.
        '''
        try:
            self._db_cursor.execute(f'''
                INSERT INTO {self._format_discordID(discordID)}(name, startdate, enddate)
                VALUES
                (?, ?, ?)
            ''', (name, startdate, enddate))
            self._db_connection.commit()
            return True
        except:
            return False

    def _format_discordID(self, discordID: int) -> str:
        '''
        Prepends 'a' to the discordID for compatibility with sqlite3.
        '''
        return ('a' + str(discordID))
    
    def _unformat_discordID(self, formatted_discordID: str) -> int:
        '''
        Removes the 'a' from the formatted discordID for frontend.
        '''
        return int(formatted_discordID[1:])

    
    def get_number_tasks(self, discordID: int) -> int:
        '''
        returns the number of tasks for a user.
        '''
        try:
            self._db_cursor.execute(f"SELECT COUNT(*) FROM {self._format_discordID(discordID)}")
            result = self._db_cursor.fetchone()[0]
            return result
        except:
            return 0
    
    def get_user(self, discordID: int) -> Union[dict[str, Any], None]:
        '''
        Returns the user's data, or None if user doesn't exist.

        {"discordID": int, "timezone": str}
        '''
        try:
            self._db_cursor.execute(f"SELECT * FROM Users WHERE discordID='{self._format_discordID(discordID)}'")
            result = self._db_cursor.fetchone()
            if result is None:
                return None
            return {"discordID": self._unformat_discordID(result[0]), "timezone": result[1]}
        except:
            return None

    def get_user_tasks(self, discordID: int) -> list[dict[str, Any]]:
        '''
        Returns a  list of the user's tasks sorted by startdate.

        [{"name": str, "startdate": int, "enddate": int}, ...]
        '''
        try:
            self._db_cursor.execute(f"SELECT * FROM {self._format_discordID(discordID)} ORDER BY startdate ASC")
            result = self._db_cursor.fetchall()
            r = []
            for task in result:
                r.append({"name": task[0], "startdate": task[1], "enddate": task[2]})
            return r
        except:
            return []
    
    def edit_user_timezone(self, discordID: int, timezone: str) -> bool:
        '''
        Updates the user's timezone.

        Returns success.
        '''
        try:
            self._db_cursor.execute(f"UPDATE Users SET timezone='{timezone}' WHERE discordID='{self._format_discordID(discordID)}'")
            self._db_connection.commit()
            return True
        except:
            return False

    def remove_task(self, discordID: int, taskIndex: int) -> bool:
        '''
        Removes the task from discordID's tasks.

        Returns success.
        '''
        try:
            self._db_cursor.execute(f'''DELETE FROM {self._format_discordID(discordID)} WHERE rowid=(SELECT rowid FROM {self._format_discordID(discordID)} ORDER BY startdate ASC LIMIT 1 OFFSET {taskIndex})''')
            self._db_connection.commit()
            return True
        except:
            return False


if __name__ == "__main__":
    # DATABASE TESTING
    database = tasksDatabase("./tasks.db")
    print(database.add_new_user(123, "EST"))
    print(database.add_new_task(123, "CSC148 task 1", 123456, 123456))
    print(database.add_new_user(5593, "GST"))
    print(database.add_new_task(123, "CSC148 task 3", 999999, 999999))
    print(database.add_new_task(5593, "MAT102 Exam", 100000, 100120))
    print(database.add_new_task(123, "CSC148 task 2", 888888, 888888))
    print(database.get_user(123) == {'discordID': 123, 'timezone': 'EST'})
    print(database.get_number_tasks(123) == 3)
    print(database.get_number_tasks(5593) == 1)
    print(database.get_user_tasks(123) == [{'name': 'CSC148 task 1', 'startdate': 123456, 'enddate': 123456}, {'name': 'CSC148 task 2', 'startdate': 888888, 'enddate': 888888}, {'name': 'CSC148 task 3', 'startdate': 999999, 'enddate': 999999}])
    print(database.remove_task(123, 1))
    print(database.edit_user_timezone(5593, "UTC"))
    print(database.get_user(123) == {'discordID': 123, 'timezone': 'EST'})
    print(database.get_number_tasks(123) == 2)
    print(database.get_user(5593) == {'discordID': 5593, 'timezone': 'UTC'})
    print(database.get_number_tasks(5593) == 1)
    print(database.get_user_tasks(123) == [{'name': 'CSC148 task 1', 'startdate': 123456, 'enddate': 123456}, {'name': 'CSC148 task 3', 'startdate': 999999, 'enddate': 999999}])
    print(database.remove_task(123, 1))
    print(database.get_user_tasks(123) == [{'name': 'CSC148 task 1', 'startdate': 123456, 'enddate': 123456}])
