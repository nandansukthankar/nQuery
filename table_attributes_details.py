import utility


class TableAttributesDetails:
    def __init__(self, db, table_details, overall_details, clauses):
        self.db = db
        self.attr_table_with_tag_map = dict()
        self.attr_table_without_tag_map = dict()

        self.overall_details = overall_details
        self.table_details = table_details
        self.clauses = clauses

    def collect(self):
        self.map_nouns_to_attributes()
        self.clauses.table_set = self.table_details.table_set
        self.clauses.table_attr_map_tags = self.attr_table_with_tag_map

    # Till the noun is mapped to its corresponding attr, attr of where_clause/order_by_clause object contains noun
    # Once mapping is done, this func replaces that noun with attr
    def replace_noun_by_attr(self, noun, attr, table, clause_flag=""):
        clause = ""
        if clause_flag == "where":
            clause = self.clauses.where_clause
        elif clause_flag == "order by":
            clause = self.clauses.order_clause
        elif clause_flag == "aggregate":
            clause = self.clauses.aggregate_clause
        elif clause_flag == "group":
            clause = self.clauses.group_by_clause
        elif clause_flag == "insert":
            clause = self.clauses.insert_clause
        elif clause_flag == "set":
            clause = self.clauses.set_clause

        for element in clause:
            if element.attr_name == noun:
                element.attribute_flag = 1
                element.table = table
                element.attr_name = attr
            if clause_flag == "where":
                if element.constant == noun:
                    element.constant = attr

    # Add the attributes, table and tags to the maps, which would be used in the final query formation
    def add_to_attribute_table_map(self, table, attr, clause_tag):
        key = table
        self.attr_table_with_tag_map.setdefault(key, [])
        self.attr_table_without_tag_map.setdefault(key, [])
        for clause in clause_tag:
            attr_clause = [attr, clause]
            if attr_clause not in self.attr_table_with_tag_map[key]:  # Don't add duplicates in the maps
                self.attr_table_with_tag_map[key].append(attr_clause)
                self.attr_table_without_tag_map[key].append(attr)
        print("Table: ", table, " Attr: ", attr)

    # wrapper function to add attribute to map
    def add_noun_attr_tn_wrapper(self, table_name, noun_value, attr):
        # add to the map of table and attr
        self.add_to_attribute_table_map(table_name, attr, self.clauses.noun_map[noun_value])

        # if the noun whose attribute is to be found is WHERE clause attr,
        # replace that noun from whereClause array with its corresponding attr
        # e.g. credit is replaced by tot_cred

        if "W" in self.clauses.noun_map[noun_value]:
            self.replace_noun_by_attr(noun_value, attr, table_name, "where")

        if "O" in self.clauses.noun_map[noun_value]:
            self.replace_noun_by_attr(noun_value, attr, table_name, "order by")

        self.replace_noun_by_attr(noun_value, attr, table_name, "aggregate")
        self.replace_noun_by_attr(noun_value, attr, table_name, "group")
        if self.clauses.type_flag["I"] == 1:
            self.replace_noun_by_attr(noun_value, attr, table_name, "insert")
        if self.clauses.type_flag["U"] == 1:
            self.replace_noun_by_attr(noun_value, attr, table_name, "set")

    # ------------------------------------------------------------------------
    # ALGO:
    # 1. If noun is a combined noun(name student) and similar table found in table set (student)
    # then corresponding attribute can be either array[0] (name)
    # or combination of combined noun (stud_name or name_stud or studName or nameStud) of that table
    # 2. If noun is a combined noun(name depart) and similar table not found in table set
    # then corresponding attribute can be in table (student) of table set only as
    # combination of combined noun (dept_name)
    # If above 2 cases does not work (found flag = 0), attribute can be in tables other than table set
    # Carry out above 2 steps with all tables other than in table set
    # NOTE - make functions for 1 and 2
    # ------------------------------------------------------------------------

    def map_compound_nouns_to_attributes(self, array, noun_para, table_name_para):
        found_flag = 0
        return_value_array = utility.Utility.check_substring_table(noun_para, table_name_para)
        if return_value_array[0]:  # if true

            if return_value_array[1] in array:  # if present in array e.g. student present in array
                array.remove(return_value_array[
                                 1])  # remove table name e.g. remove student from array, now array->[name, name student]
            table_found_flag = 1  # setting table found flag to 1

        else:
            table_found_flag = 0  # set to 0 as no table found in table set similar to noun_para

        if table_found_flag == 1:  # name depart AND department - If noun_para and similar table is found in table set
            table_found_flag = 0  # Reset flag for next loop

            # Loop over every attribute of table table name
            for attribute in self.overall_details.table_attr_map[table_name_para]:
                # print("***", table_name_para, noun_para)
                # check if array[0] i.e. name (in our e.g.) and attribute are a perfect match
                if utility.Utility.check_substring_attr(array[0], attribute, "perfect_match"):
                    # print("1")
                    self.add_noun_attr_tn_wrapper(table_name_para, noun_para, attribute)
                    found_flag = 1  # mapping for noun_para and its corresponding attribute found in table set
                    # break
                # check if attribute is made up of combined noun_para e.g. attr is stud_name and noun_para is name student
                elif utility.Utility.check_substring_attr(noun_para, attribute, "substring_match",
                                          "both_match"):
                    # print("2")
                    self.add_noun_attr_tn_wrapper(table_name_para, noun_para, attribute)

                    found_flag = 1

        else:  # name depart AND student - If noun_para and similar table is not found in table set
            for attribute in self.overall_details.table_attr_map[table_name_para]:
                if utility.Utility.check_substring_attr(noun_para, attribute, "substring_match",
                                        "both_match"):  # In such case attribute name has to be dep_name
                    # print("3")
                    self.add_noun_attr_tn_wrapper(table_name_para, noun_para, attribute)

                    found_flag = 1
                    # break
        return found_flag

    # ------------------------------------------------------------
    # ALGO:
    # 1. If noun is single word (credits) then its corresponding attr can be either as perfect match with attribute
    # or substring match with attribute (tot_cred)
    # Check for above condition first in tables of table set.
    # If not found in table set, check cond 1 in tables outside table set
    # ------------------------------------------------------------
    def map_single_nouns_to_attributes(self, noun_para, table_name_para):
        # print(">>", noun_para, table_name_para)
        found_flag = 0
        # if noun is branch, table set has branch - only branch name (primary key) should be mapped
        if utility.Utility.stem(noun_para) == utility.Utility.stem(table_name_para):
            # print("5")
            attribute = self.overall_details.get_primary_key(table_name_para)[0]
            self.add_noun_attr_tn_wrapper(table_name_para, noun_para, attribute)
            return 1
        # traverse through all attr of a table
        for attribute in self.overall_details.table_attr_map[table_name_para]:
            # print("---", noun_para, attribute)

            if utility.Utility.check_substring_attr(noun_para, attribute, "perfect_match"):  # check
                # print("6")
                self.add_noun_attr_tn_wrapper(table_name_para, noun_para, attribute)

                found_flag = 1  # found in table set

            elif utility.Utility.check_substring_attr(noun_para, attribute, "substring_match"):
                # print("7")
                # print("primary key: ", self.overall_details.get_primary_key(table_name_para))
                self.add_noun_attr_tn_wrapper(table_name_para, noun_para, attribute)

                found_flag = 1  # found in table set
        return found_flag

    def map_nouns_to_attributes(self):
        # CONSTRUCT ATTRIBUTES SET
        # handle case if attribute is not present in table set tables for 'if' and 'else'

        # This for loop maps every noun of noun map to attribute from table of table set or table attr map
        for noun in self.clauses.noun_map.keys():
            found_flag = 0
            print("Mapping noun: ", noun)
            array = noun.split()  # splitting noun by space e.g. name student makes array->[name, student]

            if len(array) > 1:  # if noun has space i.e. combined noun e.g. name student
                array.append(noun)  # appending compond noun. now array->[name, student, name student]
                # print(array, "1")

                for table_name in self.table_details.table_set:

                    temp_found_flag = self.map_compound_nouns_to_attributes(array, noun, table_name)

                    if found_flag == 0 and temp_found_flag == 1:
                        found_flag = 1

                if found_flag == 0:  # if noun and its corresponding attribute cannot be mapped to any table from table set

                    for table_name in self.overall_details.table_attr_map.keys():
                        if table_name not in self.table_details.table_set:
                            found_flag = self.map_compound_nouns_to_attributes(array, noun, table_name)

                            if found_flag == 1:
                                self.table_details.table_set.append(table_name)

            # if noun is a single word
            else:

                # first, traverse through all tables of table set
                for table_name in self.table_details.table_set:
                    # print()
                    temp_found_flag = self.map_single_nouns_to_attributes(noun, table_name)

                    if found_flag == 0 and temp_found_flag == 1:
                        found_flag = 1

                # if corresponding attr for noun is not found in table set
                if found_flag == 0:
                    # traverse for all tables of map
                    for table_name in self.overall_details.table_attr_map.keys():
                        if table_name not in self.table_details.table_set:
                            found_flag = self.map_single_nouns_to_attributes(noun, table_name)

                            if found_flag == 1:
                                self.table_details.table_set.append(table_name)  # break???

    def get_corresponding_attribute(self, table1, table2):
        related_tables_array = self.get_referenced_tables_attributes(self.db, table1)
        for entry in related_tables_array:
            if entry[0] == table2:
                return entry[1]
        related_tables_array = self.get_referenced_tables_attributes(self.db, table2)
        for entry in related_tables_array:
            if entry[0] == table1:
                return entry[2]

    def replace_table_attribute_in_clause(self, clause_array, table, subset_map):
        for clause in clause_array:
            if clause.table == table:
                clause.table = subset_map[table]
                attribute = self.get_corresponding_attribute(table, subset_map[table])
                if attribute:
                    clause.attr_name = attribute

    """
    ALGO:
    This function deletes the entries for all the tables with table name as keys of subset_map from
        map of table and attributes without clause tag
        map of table and attributes with clause tag
        table set
    Also it replaces the table that is being removed by its corresponding value from subset_map in where clause objects
    """

    # remove the tables in subset_map from table set, attribute table maps and substitute in where clause table column
    def delete_redundant_tables(self, subset_map):
        for t in subset_map.keys():
            del self.attr_table_without_tag_map[t]
            del self.attr_table_with_tag_map[t]
            self.table_details.table_set.remove(t)
            # This loop replaces the table that is to be removed from where clause
            self.replace_table_attribute_in_clause(self.clauses.where_clause, t, subset_map)
            self.replace_table_attribute_in_clause(self.clauses.order_clause, t, subset_map)
            self.replace_table_attribute_in_clause(self.clauses.aggregate_clause, t, subset_map)
            self.replace_table_attribute_in_clause(self.clauses.group_by_clause, t, subset_map)
            self.replace_table_attribute_in_clause(self.clauses.insert_clause, t, subset_map)
            self.replace_table_attribute_in_clause(self.clauses.set_clause, t, subset_map)

    # Find relations between the tables in the table set
    def create_linked_table_array(self):
        linked_array = []
        for table in self.table_details.table_set:
            related_tables_array = self.get_referenced_tables_attributes(self.db, table)
            for entry in related_tables_array:
                if entry[0] in self.table_details.table_set:
                    linked_array.append([table, entry[0], entry[1], entry[2]])
        return linked_array

    # Temporary change of attribute for checking for subsets
    def change_attribute(self, table, from_attr, to_attr):
        for i in range(0, len(self.attr_table_without_tag_map[table])):
            if self.attr_table_without_tag_map[table][i] == from_attr:
                self.attr_table_without_tag_map[table][i] = to_attr

    def remove_if_subset(self, table1, table2, subset_map):
        temp_set1 = set(self.attr_table_without_tag_map[table1])
        temp_set2 = set(self.attr_table_without_tag_map[table2])
        if temp_set1.issubset(temp_set2):
            subset_map[table1] = table2

    # Given a table name, check for subset presence in the table set
    def get_subset(self, table, subset_map):
        flag = 0
        for table_name in self.attr_table_without_tag_map.keys():
            if table_name in subset_map.keys() and subset_map[table_name] == table:
                continue
            if table == table_name:
                continue
            if table in self.attr_table_without_tag_map.keys() and table_name in self.attr_table_without_tag_map.keys():
                temp_set1 = set(self.attr_table_without_tag_map[table])
                temp_set2 = set(self.attr_table_without_tag_map[table_name])
                if temp_set1.issubset(temp_set2):
                    subset_map[table] = table_name
                    flag = 1
        return subset_map, flag

    # create a count map of all the tables which are linked, present in linked table array
    def create_table_count_map(self, linked_array):
        table_count_map = dict()
        for entry in linked_array:
            if entry[0] not in table_count_map.keys():
                table_count_map[entry[0]] = 0
            if entry[1] not in table_count_map.keys():
                table_count_map[entry[1]] = 0
            table_count_map[entry[0]] += 1
            table_count_map[entry[1]] += 1
        for table_name in self.table_details.table_set:
            if table_name not in table_count_map.keys():
                table_count_map[table_name] = 0
        return table_count_map

    # If same attribute having the same tag is present in two tables, after the filter has been applied, then
    # only one is kept, of the primary key table
    def clean_up_attributes(self, subset_map):
        linked_array = self.create_linked_table_array()
        table_count_map = self.create_table_count_map(linked_array)
        for entry in linked_array:
            if entry[0] in self.attr_table_with_tag_map.keys() and entry[1] in self.attr_table_with_tag_map.keys():
                for element in self.attr_table_with_tag_map[entry[0]]:
                    if element in self.attr_table_with_tag_map[entry[1]]:
                        self.attr_table_with_tag_map[entry[1]].remove(element)
                        self.attr_table_without_tag_map[entry[1]].remove(element[0])

        for table1 in self.attr_table_with_tag_map.keys():
            if table_count_map[table1] == 0:
                for table2 in self.attr_table_with_tag_map.keys():
                    if table1 == table2:
                        continue
                    for element in self.attr_table_with_tag_map[table1]:
                        if element in self.attr_table_with_tag_map[table2]:
                            self.attr_table_with_tag_map[table1].remove(element)
                            self.attr_table_without_tag_map[table1].remove(element[0])
                            self.remove_if_subset(table1, table2, subset_map)
        self.delete_redundant_tables(subset_map)

    def filter(self):
        no_link_flag = 0            # if there exists any table which is not linked, then 1
        flag = 0                    # if removed by subset, then 1
        change_flag = 0
        subset_map = dict()
        filter_flag = ""
        linked_array = self.create_linked_table_array()
        table_count_map = self.create_table_count_map(linked_array)
        # print("table_count_map", table_count_map)
        print("linked_array", linked_array)
        for entry in linked_array:
            # if table is in linked array, i.e. the two tables are linked
            filter_flag = "linked"
            # if table entries are present in the attribute-table map
            if entry[1] in self.attr_table_without_tag_map.keys() and \
                            entry[0] in self.attr_table_without_tag_map.keys():
                # if the attributes through which the tables are linked, are present in the attribute-table map
                if entry[2] in self.attr_table_without_tag_map[entry[1]] and \
                                entry[3] in self.attr_table_without_tag_map[entry[0]]:
                    # check if attribute names are same in both tables or no.
                    # if different, change the name temporarily, if same, keep same
                    # check for subsets
                    # change the names back to original ones
                    #filter_flag = "linked_attribute_same"
                    if entry[2] != entry[3]:
                        self.change_attribute(entry[1], entry[2], entry[3])
                        change_flag = 1
                    temp_set1 = set(self.attr_table_without_tag_map[entry[0]])
                    temp_set2 = set(self.attr_table_without_tag_map[entry[1]])
                    # if count of table is less, then it can be checked for subset
                    if table_count_map[entry[0]] < table_count_map[entry[1]]:
                        if temp_set1.issubset(temp_set2):
                            subset_map[entry[0]] = entry[1]
                    elif table_count_map[entry[0]] > table_count_map[entry[1]]:
                        if temp_set2.issubset(temp_set1):
                            subset_map[entry[1]] = entry[0]
                    else: # improve
                        if temp_set1.issubset(temp_set2):
                            subset_map[entry[0]] = entry[1]
                        elif temp_set2.issubset(temp_set1):
                            subset_map[entry[1]] = entry[0]
                    if change_flag == 1:
                        self.change_attribute(entry[1], entry[3], entry[2])
                        change_flag = 0
            # if tables in set are linked, but one table is not linked i.e. instructor, teaches and course
            # instructor and teaches are linked, but the attributes through which they are linked are not present in
            # attr-table map, then check for subset for all tables except those which are linked
            if filter_flag == "linked":
                for table in self.table_details.table_set:
                    if table_count_map[table] == 0:
                        no_link_flag = 1
                        [subset_map, flag] = self.get_subset(table, subset_map)
                    if flag == 0 and no_link_flag == 1:
                        for table in self.table_details.table_set:
                            [subset_map, flag] = self.get_subset(table, subset_map)
        # if not linked, then direct check for subset
        if filter_flag == "":
            for table in self.table_details.table_set:
                    [subset_map, flag] = self.get_subset(table, subset_map)
        # print("subset_map", subset_map)
        self.delete_redundant_tables(subset_map)
        subset_map = dict()
        self.clean_up_attributes(subset_map)

    # Refines the list of tables using 2 filters
    def filter_redundant_tables(self):
        self.filter()

    # Executes the query that returns the list of tables that use PK of t_name as their FK
    @staticmethod
    def get_referenced_tables(db, table_name):
        result = db.execute_query("SELECT distinct(TABLE_NAME) FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE "
                         "REFERENCED_TABLE_SCHEMA = '" + db.database_name + "' AND REFERENCED_TABLE_NAME = '" + table_name + "'")
        return result

    # Executes query that gives the array of records each consisting of
    #   0-referenced table,
    #   1-attribute,
    #   2-what the attribute is stored as in the referenced table
    # Referenced table is the table that uses PK of t_name as its FK
    @staticmethod
    def get_referenced_tables_attributes(db, t_name):
        result = db.execute_query("SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_COLUMN_NAME FROM "
                         "INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE REFERENCED_TABLE_SCHEMA = '" + db.database_name + "' "
                                                                                                             "AND REFERENCED_TABLE_NAME = '" + t_name + "';")
        return result