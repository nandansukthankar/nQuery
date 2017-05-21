# Give the department name and maximum salary of instructor where maximum salary of instructor is greater than 50000
# SELECT DISTINCT instructor.dep_name, SUM(instructor.salary), MAX(instructor.salary) FROM instructor
# WHERE instructor.dep_name = 'Biology' GROUP BY instructor.dep_name
# SELECT DISTINCT instructor.dep_name, SUM(instructor.salary), MAX(instructor.salary) FROM instructor
# GROUP BY instructor.dep_name HAVING MAX(instructor.salary) > 50000

# total and max of salary - handle
# Find instructor id whose salary is max salary
import table_attributes_details


class Clauses:

    def __init__(self, db):
        self.db = db
        self.implicit_hash_map = dict()
        self.constant_list = []
        self.where_clause = []
        self.order_clause = []
        self.aggregate_clause = []
        self.group_by_clause = []
        self.having_clause = []
        self.limit_clause = ""
        self.insert_clause = []
        self.update_clause = []
        self.set_clause = []

        self.order_default_list = []
        self.noun_map = dict()
        self.verb_list = list()
        self.table_set = list()
        self.table_attr_map_tags = dict()
        
        self.type_flag = dict()
        self.clause_flag = dict()
        self.init_type()
        self.init_clause_flag_dict()
        self.where_count = 0
        self.where_clause_records_count = 0
        self.between_flag = 0

    def init_type(self):
        self.type_flag["S"] = 1
        self.type_flag["I"] = 0
        self.type_flag["U"] = 0
        self.type_flag["D"] = 0

    # Initializes the flags
    def init_clause_flag_dict(self):
        self.clause_flag["S"] = 1  # If 1, the resultant query contains a SELECT Clause
        self.clause_flag["F"] = 0  # If 1, The resultant query contains a FROM Clause
        self.clause_flag["W"] = 0  # If 1, The resultant query contains a WHERE Clause
        self.clause_flag["O"] = 0  # If 1, The resultant query contains a ORDER BY Clause
        self.clause_flag["G"] = 0  # If 1, The resultant query contains a GROUP BY Clause
        self.clause_flag["H"] = 0  # If 1, The resultant query contains a HAVING Clause
        self.clause_flag["L"] = 0  # If LIMIT is present
        self.clause_flag["I"] = 0  # If insert is present
        self.clause_flag["D"] = 0  # If delete is present
        self.clause_flag["U"] = 0  # If update is present
        self.clause_flag["Set"] = 0  # If update is present

    def get_constant_expression(self, where_clause_object):
        expression = ""
        expression += "( " + "SELECT" + " " + where_clause_object.aggr + "(" + where_clause_object.table + "." + \
            where_clause_object.attr_name + ")" + " FROM" + " " + where_clause_object.table + " )"
        return expression

    def check_in_order_by(self, select_clause):
        for element in self.order_clause:
            select_clause += " " + element.table + "." + element.attr_name + ","
        return select_clause

    def remove_last_char(self, string):
        return string[0:len(string) - 1]

    def add_relation_tables(self):
        temp_map = dict()
        break_flag = 0
        for table1 in self.table_set:
            for table2 in self.table_set:
                if table1 == table2:
                    continue
                if table1 in temp_map.keys() and temp_map[table1] == table2:
                    continue
                temp_map[table2] = table1
                related_tables_array1 = table_attributes_details.TableAttributesDetails.get_referenced_tables(self.db,
                                                                                                              table1)
                related_tables_array2 = table_attributes_details.TableAttributesDetails.get_referenced_tables(self.db,
                                                                                                              table2)
                print("rel_array12", table1, table2, related_tables_array1, related_tables_array2)
                for table3 in related_tables_array1:
                    for table4 in related_tables_array2:
                        if table3 == table4 and table3 not in self.table_set:
                            self.table_set.append(table3)
                            break_flag = 1
                            break
                        related_tables_array3 = table_attributes_details.TableAttributesDetails.get_referenced_tables(
                            self.db, table3)
                        related_tables_array4 = table_attributes_details.TableAttributesDetails.get_referenced_tables(
                            self.db, table4)
                        print("rel_array34", table3, table4, related_tables_array3, related_tables_array4)
                        if table3 in related_tables_array4:
                            self.table_set.append(table3)
                            break_flag = 1
                            break
                        if table4 in related_tables_array3:
                            self.table_set.append(table4)
                            break_flag = 1
                            break
                    if break_flag == 1:
                        break

    # The template of the final SQL Query using the found attributes and table sets
    def create_query(self):

        if self.type_flag["S"] == 1:
            select_clause, from_clause, where_clause, order_clause, group_by_clause, \
                having_clause, limit_clause = "", "", "", "", "", "", ""
            if self.clause_flag["S"] == 1:
                select_clause = self.create_select_clause()

            if self.clause_flag["F"] == 1:
                from_clause = self.create_from_clause()

            if self.clause_flag["W"] == 1:
                where_clause = self.create_where_clause(1)

            if self.clause_flag["O"] == 1:
                order_clause = self.create_order_clause()

            if self.clause_flag["G"] == 1:
                group_by_clause = self.create_group_by_clause()

            if self.clause_flag["H"] == 1:
                having_clause = self.create_having_clause()

            if self.clause_flag["L"] == 1:
                limit_clause = self.create_limit_clause()

            final_query = select_clause + from_clause + where_clause + order_clause + group_by_clause + \
                          having_clause + limit_clause

            return final_query, "S"

        elif self.type_flag["I"] == 1:
            insert_clause = ""
            if self.clause_flag["I"] == 1:
                insert_clause = self.create_insert_clause()

            final_query = insert_clause

            return final_query, "I"

        elif self.type_flag["D"] == 1:
            delete_clause, where_clause = "", ""
            if self.clause_flag["D"] == 1:
                delete_clause = self.create_delete_clause()

            if self.clause_flag["W"] == 1:
                where_clause = self.create_where_clause(1)

            final_query = delete_clause + where_clause

            return final_query, "D"

        elif self.type_flag["U"] == 1:
            update_clause, set_clause, where_clause = "", "", ""
            if self.clause_flag["U"] == 1:
                update_clause = self.create_update_clause()

            if self.clause_flag["Set"] == 1:
                set_clause = self.create_set_clause()

            if self.clause_flag["W"] == 1:
                where_clause = self.create_where_clause(1)

            final_query = update_clause + set_clause + where_clause

            return final_query, "U"

    def create_update_clause(self):
        update_clause = "UPDATE"
        update_clause += " " + self.table_set[0]
        return update_clause

    def create_set_clause(self):
        set_clause = " SET"
        for element in self.set_clause:
            set_clause += " " + element.table + "." + element.attr_name + " = " + element.value + ","
        set_clause = self.remove_last_char(set_clause)
        return set_clause

    def create_delete_clause(self):
        delete_clause = "DELETE FROM"
        delete_clause += " " + self.table_set[0]
        return delete_clause

    def create_insert_clause(self):
        error = False
        table = ""
        column_string, values_string = "(", "("
        insert_clause = "INSERT INTO"
        if len(self.table_set) == 1:
            table = self.table_set[0]
        for element in self.insert_clause:
            if element.table != table:
                error = True
                break
        if not error:
            for element in self.insert_clause:
                column_string += " " + element.table + "." + element.attr_name + ","
                values_string += " '" + element.value + "' ,"
            column_string = self.remove_last_char(column_string)
            values_string = self.remove_last_char(values_string)
            column_string += " )"
            values_string += ")"

            insert_clause += " " + table + " " + column_string + " VALUES " + values_string
        else:
            insert_clause = ""

        return insert_clause

    def create_select_clause(self):
        # Construct SELECT Clause
        non_aggr = ""
        select_clause = "SELECT"

        # select clause can consist of aggregate func
        aggr_str = AggregateClause.get_aggregate(self)

        # If the tag associated with an attribute is 'S', append the attributes along with the table name
        for table in self.table_attr_map_tags.keys():

            for array_element in self.table_attr_map_tags[table]:

                if array_element[1] == "S":
                    # check if the attribute is already covered in aggregate string
                    flag = AggregateClause.check_if_in_aggregate(self, array_element[0], table)

                    if not flag:
                        non_aggr += " " + table + "." + array_element[0] + ","

        if non_aggr == "" and aggr_str != "": # only aggregate
            select_clause += self.remove_last_char(aggr_str)
        elif non_aggr != "" and aggr_str == "": # only non aggregate
            select_clause += " DISTINCT" + self.remove_last_char(non_aggr)
        elif non_aggr != "" and aggr_str != "": # both
            select_clause += " DISTINCT" + non_aggr + self.remove_last_char(aggr_str)
        else: # no attribute found
            if self.clause_flag["O"] == 1:
                select_clause += " DISTINCT"
                select_clause = self.remove_last_char(self.check_in_order_by(select_clause))
            else:
                select_clause += " *"
        return select_clause

    def create_group_by_clause(self):
        group_by_clause = " GROUP BY"
        for element in self.group_by_clause:
            if element.attribute_flag == 1:
                group_by_clause += " " + element.table + "." + element.attr_name + ","
        if group_by_clause == " GROUP BY":
            group_by_clause = ""
        else:
            group_by_clause = self.remove_last_char(group_by_clause)
        return group_by_clause

    def create_having_clause(self):
        return self.create_where_clause(0)

    def create_from_clause(self):
        # Construct FROM Clause
        #self.add_relation_tables()
        from_clause = " FROM"
        linked_flag = 0
        first_inner = 0
        inner_join_flag = 0
        length = len(self.table_set)
        if length == 1:
            from_clause += " " + self.table_set[0]
            return from_clause
        for table in self.table_set:
            related_tables_array = self.get_referenced_tables_attributes(table)
            if len(related_tables_array) > 0:
                for entry in related_tables_array:
                    if entry[0] in self.table_set:
                        linked_flag = 1
                        if entry[1] != entry[2]:
                            inner_join_flag = 1

        if inner_join_flag == 0 and linked_flag == 1:
            for table in self.table_set:
                if length == 1:
                    from_clause += " " + table  # If one table is present, append it to the FORM clause
                else:
                    length -= 1
                    from_clause += " " + table + " NATURAL JOIN"  # If more tables present, Use Natural Join (tentative)

        elif inner_join_flag == 1:
            for table in self.table_set:
                related_tables_array = self.get_referenced_tables_attributes(table)
                for entry in related_tables_array:
                    if entry[0] in self.table_set:
                        if first_inner == 0:
                            first_inner = 1
                            from_clause += " " + table + " " + "INNER JOIN" + " " + entry[
                                0] + " " + "ON" +" " + table + "." \
                                           + entry[2] + " = " + entry[0] + "." + entry[1]
                        else:
                            from_clause += " " + "INNER JOIN" + " " + table + " " + "ON" + " " + table + "." + \
                                           entry[2] + " = " + entry[0] + "." + entry[1]
        else: # cartesian product
            for table in self.table_set:
                from_clause += " " + table + ","
            from_clause = self.remove_last_char(from_clause)
        return from_clause

    def create_limit_clause(self):
        limit_clause = " LIMIT"
        limit_clause += " " + self.limit_clause
        return limit_clause

    def create_order_clause(self):
        temp = ""
        order_clause = " ORDER BY"
        length = len(self.order_clause)
        if length == 0:  # attribute not found... hence use select clause attributes
            for table in self.table_attr_map_tags.keys():
                for array_element in self.table_attr_map_tags[table]:
                    if array_element[1] == "S":
                        temp += " " + table + "." + array_element[0] + ","
            order_clause += self.remove_last_char(temp) + " " + self.order_default_list[0]  #
        else:
            for element in self.order_clause:
                if length == 1:
                    order_clause += " " + element.table + "." + element.attr_name + " " + element.order
                else:
                    length -= 1
                    order_clause += " " + element.table + "." + element.attr_name + " " + element.order + ","
                    # If more tables present, Use Natural Join (tentative)
        return order_clause

    """
    ALGORITHM:
    if clause_flag["W"] == 1, then our query contains a where clause.
        length is the length of where clause object array, which is decremented after one iteration
        Traverse each record in whereClause objects array (object of class WhereClauseContent)
            if we want to skip the iteration of the main for loop, i.e. loop_flag == 1, then continue
            if length == 1, i.e only one object remains in whereClause,
                form where_clause query
                check for bracket_flag, i.e. if 1,(open bracket was inserted), then put closing bracket
            else (if length variable is more than 1)
                check for "BETWEEN" conjunction in objects
                    insert open bracket
                    make loop_flag 1, decrement length by 2; i.e skip iteration
                    form the between clause query
                    insert closing bracket
                if there is no "BETWEEN" and length is more than 1
                    if the 'count' variable of current and next record is same, if open bracket is not yet inserted
                        insert open bracket and set bracket_flag
                    decrement the variable length
                    form the appropriate where clause syntax
                    if next count is different from present, and open bracket was given
                        insert closing bracket, reset bracket flag
                    if next count is the same as present, but bracket flag is 1
                        do nothing, don't close bracket
                    insert the conjunction in syntax
    """

    def create_where_clause(self, use_where):
        # Construct WHERE Clause
        skip_loop_flag = 0  # skip_loop_flag 1 means skip the loop and continue;set when between conjunction encountered
        # so that next where clause object is skipped (because its already used in earlier loop)
        open_bracket_flag = 0  # open_bracket_flag = 0 means no open bracket needed or brackets are balanced()
        if use_where == 1:
            clause = " WHERE"
        else:
            clause = " HAVING"
        length = len(self.where_clause)
        # for each record in where clause array
        for i in range(0, len(self.where_clause)):
            if self.where_clause[i].use_where != use_where:
                continue
            # loop flag is one, then continue, to skip the iteration, used for 'between'
            if skip_loop_flag == 1:
                skip_loop_flag = 0
                continue
            # If only one record is left
            if length == 1:

                if use_where == 0:
                    final_attr = self.where_clause[i].aggr + "(" + self.where_clause[i].table + "." + \
                                 self.where_clause[i].attr_name + ")"
                else:
                    final_attr = self.where_clause[i].table + "." + self.where_clause[i].attr_name

                if self.where_clause[i].constant_flag == 0:
                    final_const = self.get_constant_expression(self.where_clause[i])
                else:
                    final_const = "'" + self.where_clause[i].constant + "'"

                final_rel_op = self.where_clause[i].rel_op

                clause += " " + final_attr + " " + final_rel_op + " " + final_const
                if open_bracket_flag == 1:
                    clause += " )"
                    open_bracket_flag = 0

            # Multiple records
            else:
                # Between clause
                if self.where_clause[i].conjunction == "BETWEEN":
                    clause += " ("
                    length -= 2  # length reduced by 2 because BETWEEN uses next where clause object also (i+1)
                    if use_where == 0:
                        final_attr = self.where_clause[i].aggr + "(" + self.where_clause[i].table + "." + \
                                     self.where_clause[i].attr_name + ")"
                    else:
                        final_attr = self.where_clause[i].table + "." + self.where_clause[i].attr_name

                    if self.where_clause[i].constant_flag == 0:
                        final_const = self.get_constant_expression(self.where_clause[i])
                    else:
                        final_const = "'" + self.where_clause[i].constant + "'"

                    clause += " " + final_attr + " " + \
                                    self.where_clause[i].conjunction + " " + final_const + " AND '" + \
                                    self.where_clause[i + 1].constant + "'"
                    # if between clause, then close bracket is needed
                    clause += " )"
                    clause += " " + self.where_clause[i + 1].conjunction
                    skip_loop_flag = 1  # loop_flag set so that for loop is skipped for next where clause object

                else:
                    # if next count is the same as present, its part of same bracket pair
                    if self.where_clause[i].count == self.where_clause[i + 1].count and open_bracket_flag == 0:
                        clause += " ("
                        open_bracket_flag = 1

                    length -= 1
                    if use_where == 0:
                        final_attr = self.where_clause[i].aggr + "(" + self.where_clause[i].table + "." + \
                                     self.where_clause[i].attr_name + ")"
                    else:
                        final_attr = self.where_clause[i].table + "." + self.where_clause[i].attr_name

                    if self.where_clause[i].constant_flag == 0:
                        final_const = self.get_constant_expression(self.where_clause[i])
                    else:
                        final_const = "'" + self.where_clause[i].constant + "'"

                    final_rel_op = self.where_clause[i].rel_op

                    clause += " " + final_attr + " " + final_rel_op + " " + final_const

                    # if next count is different from present, and open bracket was given, then close it
                    # if next count is the same as present, but bracket flag is 1, then do nothing, don't close bracket
                    if self.where_clause[i].count != self.where_clause[i + 1].count and open_bracket_flag == 1:
                        clause += " )"
                        open_bracket_flag = 0
                    if self.where_clause[i].conjunction == "":
                        final_conj = "AND"
                    else:
                        final_conj = self.where_clause[i].conjunction
                    clause += " " + final_conj

        if clause == " WHERE" or clause == " HAVING":
            clause = ""

        return clause

    # Executes query that gives the array of records each consisting of
    #   0-referenced table,
    #   1-attribute,
    #   2-what the attribute is stored as in the referenced table
    # Referenced table is the table that uses PK of t_name as its FK
    def get_referenced_tables_attributes(self, t_name):
        result = self.db.execute_query("SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_COLUMN_NAME FROM "
                                       "INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE REFERENCED_TABLE_SCHEMA = '" + self.db.database_name + "' "
                                                                                                             "AND REFERENCED_TABLE_NAME = '" + t_name + "';")
        return result


class WhereClauseContent:
    def __init__(self, count, attr_name, rel_op, constant, conjunction="", aggr="", constant_flag=1,
                 table="",attribute_flag=0):
        self.count = count  # count is the number denoting conditions belonging to same bracket pair
        self.attr_name = attr_name  # Attribute name
        self.rel_op = rel_op  # Relational operator (default - '=')
        self.constant = constant  # Constant in the relation
        self.table = table  # table to which the attribute belongs
        self.conjunction = conjunction  # The conjunction associated with the condition
        self.use_where = 1      # this flag tells if its where object or having object, where - 1 and having - 0
        self.aggr = aggr    # if having obj, aggregate func (SUM, COUNT, etc.)
        self.constant_flag = constant_flag # states whether the constant field is filled by constant / aggregate
        self.attribute_flag = attribute_flag


    @staticmethod
    def get_having_clause(clauses):
        for where_clause_element in clauses.where_clause:
            for aggregate_clause_element in clauses.aggregate_clause:
                if where_clause_element.attr_name == aggregate_clause_element.attr_name and \
                        where_clause_element.table == aggregate_clause_element.table and \
                                aggregate_clause_element.tag == "W" and aggregate_clause_element.type == "attr":

                    where_clause_element.use_where = 0
                    clauses.clause_flag["H"] = 1
                    where_clause_element.aggr = aggregate_clause_element.aggregate
                    break

    @staticmethod
    def add_where_clause(clauses, where_count, attr, rel_op, const, conj="", aggr="", constant_flag=1, attribute_flag=0,
                         table=""):
        where_object = WhereClauseContent(where_count, attr, rel_op, const, conj, aggr=aggr, constant_flag=constant_flag,
                                          attribute_flag=attribute_flag,table=table)
        if clauses.clause_flag["W"] == 0:
            clauses.clause_flag["W"] = 1
        clauses.where_clause.append(where_object)
        clauses.where_clause_records_count += 1

    @staticmethod
    def print_where_clause(where_clause):
        print("\nWHERE clause objects:")
        for element in where_clause:
            print(element.count, element.table, element.attr_name, element.rel_op,
                  element.constant, element.conjunction, element.use_where, element.aggr, element.constant_flag,
                    "attribute:", element.attribute_flag)


class OrderByClause:
    def __init__(self, order, attr_name, table=""):
        self.order = order  # ASC / DESC
        self.attr_name = attr_name  # Attribute name
        self.table = table

    @staticmethod
    def add_order_clause(clauses, order, attr):
        order_by_object = OrderByClause(order, attr)
        clauses.order_clause.append(order_by_object)

    @staticmethod
    def print_order_by_clause(order_clause):
        print("\nORDER clause objects:")
        for element in order_clause:
            print(element.attr_name, element.order, element.table, "attribute:", element.attribute_flag)


class AggregateClause:
    def __init__(self, aggregate, attr_name, tag, type_value, table=""):
        self.aggregate = aggregate  # ASC / DESC
        self.attr_name = attr_name  # Attribute name
        self.tag = tag
        self.table = table
        self.type = type_value
        self.attribute_flag = 0

    @staticmethod
    def get_aggregate(clauses):
        aggr_str = ""
        for element in clauses.aggregate_clause:
            if element.tag == "S" and element.attribute_flag == 1:      # noun is mapped to attribute
                aggr_str += " " + element.aggregate + "( DISTINCT " + element.table + "." + element.attr_name + " ),"
            elif element.tag == "S" and element.attribute_flag == 0:
                aggr_str += " " + element.aggregate + "( " + "*" + " ),"
        return aggr_str

    @staticmethod
    def check_if_in_aggregate(clauses, attribute, table):
        for element in clauses.aggregate_clause:
            if element.table == table and element.attr_name == attribute and element.tag == "S":
                return True
        return False

    @staticmethod
    def add_aggr_attr(clauses, final_aggr, final_noun, tag, type_value="attr"):
        aggr_object = AggregateClause(final_aggr, final_noun, tag, type_value)
        clauses.aggregate_clause.append(aggr_object)

    @staticmethod
    def print_aggregate(aggregate_clause):
        print("\nAggregate objects:")
        for element in aggregate_clause:
            print(element.attr_name, element.aggregate, element.tag, element.table, element.type,
                "attribute:", element.attribute_flag)


class GroupByClause:
    def __init__(self, attr_name, table="", attribute_flag=0):
        self.attr_name = attr_name  # Attribute name
        self.table = table
        self.attribute_flag = attribute_flag

    @staticmethod
    def add_to_group_by_clause(clauses, attribute, table="", attribute_flag=0):
        if clauses.clause_flag["G"] == 0:
            clauses.clause_flag["G"] = 1
        group_by_object = GroupByClause(attribute, table=table, attribute_flag=attribute_flag)
        clauses.group_by_clause.append(group_by_object)

    @staticmethod
    def get_group_clauses(clauses):
        aggr_str = AggregateClause.get_aggregate(clauses)

        # If the tag associated with an attribute is 'S', append the attributes along with the table name
        for table in clauses.table_attr_map_tags.keys():

            for array_element in clauses.table_attr_map_tags[table]:

                if array_element[1] == "S":
                    # check if the attribute is already covered in aggregate string
                    flag = AggregateClause.check_if_in_aggregate(clauses, array_element[0], table)

                    if not flag:
                        # if there is NO AGGREGATE but there is HAVING that means GROUP BY is present
                        if aggr_str != "" or (aggr_str == "" and clauses.clause_flag["H"] == 1):
                            GroupByClause.add_to_group_by_clause(clauses, array_element[0], table=table,
                                                                 attribute_flag=1)

    @staticmethod
    def print_group_by(group_clause):
        print("\nGroup By objects:")
        for element in group_clause:
            print(element.attr_name, element.table, "attribute:", element.attribute_flag)


class InsertClause:
    def __init__(self, attr_name, value, table="", attribute_flag=0):
        self.attr_name = attr_name  # Attribute name
        self.value = value
        self.table = table
        self.attribute_flag = attribute_flag

    @staticmethod
    def add_to_insert_clause(clauses, attribute, value, table="", attribute_flag=0):
        if clauses.clause_flag["I"] == 0:
            clauses.clause_flag["I"] = 1
        insert_object = InsertClause(attribute, value, table=table, attribute_flag=attribute_flag)
        clauses.insert_clause.append(insert_object)

    @staticmethod
    def print_insert(insert_clause):
        print("\nInsert objects:")
        for element in insert_clause:
            print(element.attr_name, element.value, element.table, "attribute:", element.attribute_flag)


class SetClause:
    def __init__(self, attr_name, value, table="", attribute_flag=0):
        self.attr_name = attr_name  # Attribute name
        self.value = value
        self.table = table
        self.attribute_flag = attribute_flag

    @staticmethod
    def add_to_set_clause(clauses, attribute, value, table="", attribute_flag=0):
        if clauses.clause_flag["Set"] == 0:
            clauses.clause_flag["Set"] = 1
        set_object = SetClause(attribute, value, table=table, attribute_flag=attribute_flag)
        clauses.set_clause.append(set_object)

    @staticmethod
    def print_set(set_clause):
        print("\nSet objects:")
        for element in set_clause:
            print(element.attr_name, element.value, element.table, "attribute:", element.attribute_flag)