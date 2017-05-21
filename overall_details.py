from difflib import SequenceMatcher


class OverallDetails:
    def __init__(self, db):
        self.db = db
        self.retrieve_table_name_query = "SELECT table_name FROM information_schema.tables where table_schema='" + \
                            db.database_name + "'"
        self.tables = list()
        self.table_attr_map = dict()
        self.table_PK_map = dict()

    def collect_details(self):
        self.tables = self.get_all_tables()
        self.create_maps()

    def get_all_tables(self):
        tables = self.db.execute_query(self.retrieve_table_name_query)
        return tables

    def create_maps(self):
        for table in self.tables:
            self.table_attr_map[table] = self.get_attributes(table)
            self.table_PK_map[table] = self.get_primary_key(table)

    def get_attributes(self, table_name):
        result = self.db.execute_query("SELECT DISTINCT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='" + self.db.database_name +
                 "'AND TABLE_NAME ='" + table_name + "';")
        return result

    def get_row_for_value(self, table_name, column_name, value):
        result = self.db.execute_query(
            "SELECT " + column_name + " FROM " + table_name + " WHERE INSTR(" + column_name + ", '" + value + "') > 0")
        if len(result) > 0:
            return True
        return False

    def get_primary_key(self, table_name):
        result = self.db.execute_query("SELECT `COLUMN_NAME` FROM `information_schema`.`COLUMNS` \
        WHERE(`TABLE_SCHEMA` = '" + self.db.database_name + "') AND(`TABLE_NAME` = '" + table_name + "') AND(`COLUMN_KEY` = 'PRI')")
        return result

    def get_table_from_primary_key(self, primary_key):
        result = self.db.execute_query("SELECT GROUP_CONCAT(COLUMN_NAME), TABLE_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE \
                WHERE TABLE_SCHEMA = '"+ self.db.database_name +"' AND CONSTRAINT_NAME='PRIMARY' GROUP BY TABLE_NAME ")
        print(result)
        for element in result:
            match = SequenceMatcher(None, primary_key, element[0]).find_longest_match(0, len(primary_key), 0,
                                                                                 len(element[0]))
            if match.size == len(primary_key):
                return element[1]