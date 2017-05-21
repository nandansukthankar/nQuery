import pymysql
import sys


class Database:
    def __init__(self, server, username, password, database):
        self.server = server
        self.username = username
        self.password = password
        self.database_name = database
        self.db = None

    def connect(self):
        try:
            # Connection to the MySQL database
            self.db = pymysql.connect(self.server, self.username, self.password, self.database_name)
        except Exception:
            print("Invalid username or password")
            sys.exit(1)

    def close(self):
        if self.db.open:
            self.db.close()

    @staticmethod
    def retrieve(cursor, flag):
        if flag == "1":
            column_names = [i[0] for i in cursor.description]
            print("!!!!!!!!!!!!", column_names)
        result = list()
        temp_array = []
        for row in cursor:
            if len(row) == 1:
                result.append(str(row[0]))
            else:
                for i in range(0, len(row)):
                    temp_array.append(str(row[i]))
                result.append(temp_array)
                temp_array = []
        if flag == "0":
            return result
        else:
            return result, column_names

    def execute_query(self, sql_query, flag="0"):
        cursor = self.db.cursor()
        cursor.execute(sql_query)
        self.db.commit()
        return Database.retrieve(cursor, flag)

