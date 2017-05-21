import utility
import table_attributes_details


class TableDetails:
    def __init__(self, db):
        self.table_set = list()
        self.db = db

    def collect_tables(self, clauses, overall_details):
        self.map_nouns_verbs_to_tables(clauses, overall_details)
        self.add_relation_tables()
        return self.table_set

    # CONSTRUCT TABLES SET
    # Adds tables from table list to table set that are similar to noun from noun map
    # i.e adds tables that are LIKELY to be there in final sql query
    def map_nouns_verbs_to_tables(self, clauses, overall_details):

        for noun in clauses.noun_map.keys():

            # for every table in table list
            for table_name in overall_details.tables:
                # check if noun and table name is similar
                return_temp_value = utility.Utility.check_substring_table(noun, table_name)

                if return_temp_value[0]:  # if true

                    if table_name not in self.table_set:  # add unique table name in table set
                        print("Noun '" + noun + "' mapped to table '" + table_name + "'")
                        self.table_set.append(table_name)  # add table name to table set
                        clauses.clause_flag["F"] = 1  # set FROM clause flag to 1

        for verb in clauses.verb_list:

            for table_name in overall_details.tables:
                return_temp_value = utility.Utility.check_substring_table(verb, table_name, "verb")

                if return_temp_value[0]:  # if true

                    if table_name not in self.table_set:  # add unique table name in table set
                        print("Verb '" + verb + "' mapped to table '" + table_name + "'")
                        self.table_set.append(table_name)  # add table name to table set
                        clauses.clause_flag["F"] = 1  # set FROM clause flag to 1

    def add_relation_tables(self):
        break_flag = 0
        for table1 in self.table_set:
            for table2 in self.table_set:
                if table1 == table2:
                    continue
                related_tables_array1 = table_attributes_details.TableAttributesDetails.get_referenced_tables(self.db,
                                                                                                              table1)
                related_tables_array2 = table_attributes_details.TableAttributesDetails.get_referenced_tables(self.db,
                                                                                                              table2)
                for table in related_tables_array1:
                    if table in related_tables_array2 and table not in self.table_set:
                        self.table_set.append(table)
                        break_flag = 1
                        break
                if break_flag == 1:
                    break_flag = 0
                    break

