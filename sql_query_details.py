import table_details
import table_attributes_details
import clauses
import utility
import re


class SQLQueryDetails:

    def __init__(self, db, overall_details):
        self.db = db
        self.overall_details = overall_details
        self.clauses = clauses.Clauses(self.db)

    def collect_query_details(self, natural_lang_query):
        tokens = utility.Utility.tokenize(natural_lang_query)
        print("\nTokens: ", tokens)

        tagged_tokens = utility.Utility.tag(tokens)

        tagged_tokens = utility.Utility.convert_proper_noun_to_upper(tagged_tokens)
        print("\nTagged tokens: ", tagged_tokens)

        self.create_lists(tagged_tokens)

        self.clauses.where_count = self.set_where_count()

        if self.clauses.type_flag["S"] == 1:
            self.create_implicit_map(self.clauses.constant_list)
            print("\nImplicit_Hash_Map: ", self.clauses.implicit_hash_map)

        print("\nNoun map: ", self.clauses.noun_map)
        print("\nVerb list: ", self.clauses.verb_list)

        table_details_object = table_details.TableDetails(self.db)
        table_details_object.collect_tables(self.clauses, self.overall_details)

        print("Table set: ", table_details_object.table_set)

        table_attributes_details_object = table_attributes_details.TableAttributesDetails(self.db, table_details_object, self.overall_details, self.clauses)
        table_attributes_details_object.collect()

        print("\nBefore filtering:")
        print("Table set: ", table_details_object.table_set)
        print("Table attribute map with tags: ", table_attributes_details_object.attr_table_with_tag_map)
        print("Table attribute map without tags: ", table_attributes_details_object.attr_table_without_tag_map)

        table_attributes_details_object.filter_redundant_tables()

        if len(table_details_object.table_set) == 0:
            raise Exception('No tables')
        print("\nAfter filtering:")
        print("Table set: ", table_details_object.table_set)
        print("Table attribute map: ", table_attributes_details_object.attr_table_with_tag_map)
        print("Table attribute map without tags: ", table_attributes_details_object.attr_table_without_tag_map)

        self.finalize_clauses()

        if self.clauses.type_flag["S"] == 1:
            self.check_for_implicit(table_details_object, table_attributes_details_object)
            print("\nImplicit_Hash_Map: ", self.clauses.implicit_hash_map)

        clauses.WhereClauseContent.print_where_clause(self.clauses.where_clause)
        clauses.OrderByClause.print_order_by_clause(self.clauses.order_clause)
        clauses.AggregateClause.print_aggregate(self.clauses.aggregate_clause)
        clauses.GroupByClause.print_group_by(self.clauses.group_by_clause)
        clauses.InsertClause.print_insert(self.clauses.insert_clause)
        clauses.SetClause.print_set(self.clauses.set_clause)

        return self.clauses

    def remove_unwanted_implicit(self):
        temp_dict = dict()
        count = 0
        max_value = 0
        for constant in self.clauses.implicit_hash_map.keys():
            if self.clauses.implicit_hash_map[constant] and len(self.clauses.implicit_hash_map[constant]) != 1:
                for element in self.clauses.implicit_hash_map[constant]:
                    key = element[1]
                    if key not in temp_dict.keys():
                        temp_dict[key] = 0
                    temp_dict[key] += 1
                for key in temp_dict.keys():
                    if count == 0:
                        max_value = key
                        count += 1
                    else:
                        if temp_dict[max_value] < temp_dict[key]:
                            max_value = key
                primary_key = max_value
                table = self.overall_details.get_table_from_primary_key(primary_key)
                self.clauses.implicit_hash_map[constant] = []
                self.clauses.implicit_hash_map[constant].append([table, primary_key])

    def replace_implicit_in_where(self, table_details_object):
        for where_clause in self.clauses.where_clause:
            for constant in self.clauses.implicit_hash_map.keys():
                if where_clause.constant == constant and where_clause.attribute_flag == 0:
                    if self.clauses.implicit_hash_map[constant]:
                        where_clause.attribute_flag = 1
                        table = self.clauses.implicit_hash_map[constant][0][0]
                        attribute = self.clauses.implicit_hash_map[constant][0][1]
                        where_clause.table = table
                        where_clause.attr_name = attribute
                        if table not in table_details_object.table_set:
                            table_details_object.table_set.append(table)

    def create_where_objects_implicit(self, table_details_object, table_attributes_details_object):
        for constant in self.clauses.implicit_hash_map.keys():
            constant_present = 0
            for where_clause in self.clauses.where_clause:
                if where_clause.constant == constant:
                    constant_present = 1
                    break
            if constant_present == 0 and self.clauses.implicit_hash_map[constant]:
                attr = self.clauses.implicit_hash_map[constant][0][1]
                table = self.clauses.implicit_hash_map[constant][0][0]
                clauses.WhereClauseContent.add_where_clause(self.clauses, self.clauses.where_count, attr, "=", constant,
                                                            table=table, attribute_flag=1)
                for table_name in table_details_object.table_set:
                    if table_name not in table_attributes_details_object.attr_table_with_tag_map.keys():
                        table_details_object.table_set.remove(table_name)
                if table not in table_details_object.table_set:
                    table_details_object.table_set.append(table)

    def check_for_implicit(self, table_details_object, table_attributes_details_object):
        self.remove_unwanted_implicit()
        self.replace_implicit_in_where(table_details_object)
        self.create_where_objects_implicit(table_details_object, table_attributes_details_object)

    def create_implicit_map(self, constant_array):
        tables = self.overall_details.tables
        for constant in constant_array:
            key = constant
            self.clauses.implicit_hash_map.setdefault(key, [])
            for table in tables:
                column_list = self.overall_details.get_attributes(table)
                for column in column_list:
                    exists_flag = self.overall_details.get_row_for_value(table, column, constant)
                    tuple = [table, column]
                    if exists_flag and tuple not in self.clauses.implicit_hash_map[constant]:
                        self.clauses.implicit_hash_map[constant].append(tuple)

    def add_to_noun_map(self, noun, tag):
        self.clauses.noun_map.setdefault(noun, [])
        if tag not in self.clauses.noun_map[noun]:
            self.clauses.noun_map[noun].append(tag)

    def check_change_tag(self, temp_attr, prev_tag):
        for attribute in self.clauses.noun_map.keys():
            if attribute == temp_attr and prev_tag in self.clauses.noun_map[attribute]:
                self.clauses.noun_map[attribute].remove(prev_tag)
                self.clauses.noun_map[attribute].append("W")

        for element in self.clauses.aggregate_clause:
            if element.attr_name == temp_attr and element.tag == prev_tag:
                element.tag = "W"

    @staticmethod
    def stem_token(current_token, current_token_tag):
        if current_token_tag != "NNP" and current_token_tag != "NNPS" and current_token_tag != "CD" and \
                        current_token not in utility.Utility.break_words and \
                        current_token not in utility.Utility.rel_op_dict.keys() and \
                        current_token not in utility.Utility.order_by_dict.keys() and \
                        current_token not in utility.Utility.aggregate_of_dict.keys() and \
                        current_token not in utility.Utility.aggregate_dict.keys() and \
                        current_token not in utility.Utility.insert_array and \
                        current_token not in utility.Utility.delete_array and \
                        current_token not in utility.Utility.update_array and \
                        current_token not in utility.Utility.limit_word_dict.keys() and \
                        current_token not in utility.Utility.limit_dict.keys() and \
                        current_token not in utility.Utility.escape_array:
            return True
        else:
            return False

    def between_condition_satisfied(self, i):
        if (self.clauses.where_clause[i].rel_op == ">" and self.clauses.where_clause[i - 1].rel_op == "<"
            and utility.Utility.parse_string_to_float(self.clauses.where_clause[i].constant) <
                utility.Utility.parse_string_to_float(self.clauses.where_clause[i - 1].constant)) or \
            (self.clauses.where_clause[i].rel_op == "<" and self.clauses.where_clause[i - 1].rel_op == ">"
             and utility.Utility.parse_string_to_float(self.clauses.where_clause[i].constant) >
                    utility.Utility.parse_string_to_float(self.clauses.where_clause[i - 1].constant)) and \
                self.clauses.where_clause[i - 1].conjunction == "AND":
            return True

    def check_between_condition(self, i):
        if self.between_condition_satisfied(i):
            self.clauses.where_clause[i - 1].rel_op = "="
            self.clauses.where_clause[i - 1].conjunction = "BETWEEN"
            self.clauses.where_clause[i].rel_op = "="
            self.clauses.where_clause[i].conjunction = ""

    def change_type_in_aggregate(self, attribute, aggregate):
        for where_object in self.clauses.where_clause:
            for aggr_object in self.clauses.aggregate_clause:
                if where_object.constant_flag == 0 and aggr_object.attr_name == attribute and \
                        aggr_object.aggregate == aggregate:
                    aggr_object.type = "const"

    def set_where_count(self):
        where_count = 1
        if len(self.clauses.where_clause) == 0:
            return where_count
        for i in range(1, len(self.clauses.where_clause)):
            if self.clauses.where_clause[i].attr_name != self.clauses.where_clause[i - 1].attr_name:
                where_count += 1
                self.clauses.where_clause[i].count = where_count
            else:
                self.clauses.where_clause[i].count = where_count
                self.check_between_condition(i)
        return where_count + 1

    def noun_present_in_aggregate(self, noun):
        if self.clauses.aggregate_clause[len(self.clauses.aggregate_clause) - 1].attr_name == noun:
            return True
        return False

    # Create lists using the tokens and corresponding tags
    def create_lists(self, tagged_tokens):
        where_count = 1  # Used to assign the 'count' attribute of the where clause object
        # Used to handle a case where an attribute and rel_op value is associated with more than
        #   one constant, eg. score is between 90 and 100; or attribute value is associated with more than one pair of
        #   rel_op and constant, eg. score is greater than 100 and less than 150 (Use between in such cases)
        constant_flag = 0
        aggregate_flag = 0
        limit_flag = 0

        token_count = 0  # count of tokens in a sentence - used to handle two continuous nouns, eg. department name
        previous_count = 0
        previous_constant_count = 0
        previous_order_by_count = 0

        earlier_token_flag = ""
        temp_noun = ""
        temp_continuous_const = ""
        temp_continuous_rel_op = ""
        prev_attr, prev_rel_op = "", ""

        final_noun, final_rel_op, final_const = "", "", ""
        final_const = ""
        final_aggr = ""

        insert_attr = ""
        insert_value = ""
        update_set_attr = ""
        update_set_value = ""

        prev_tag = ""
        tag = "S"  # S - SELECT, W - WHERE
        group_by = 0

        temp_attr, temp_rel_op, temp_conj = "", "", ""
        temp_order, temp_order_attr = "", ""

        continuous_order_by_flag = 0  # to handle 'reverse alphabetical'

        for token in tagged_tokens:  # Each element 'token' is of the form (token, tag)
            current_token = token[0]
            current_token_tag = token[1]
            token_count += 1
            # Do not stem the token when it satisfies one of the cases in function 'stem_token'
            if SQLQueryDetails.stem_token(current_token, current_token_tag):
                current_token = utility.Utility.stem(current_token)

            # Indicates presence of 'group_by' clause
            if current_token == "each" or current_token == "every":
                group_by = 1
                if earlier_token_flag == "first_rel_op":
                    final_rel_op = temp_continuous_rel_op
                    earlier_token_flag = ""

                elif earlier_token_flag == "first_noun" or earlier_token_flag == "of":
                    earlier_token_flag = ""
                    final_noun = temp_noun
                    self.add_to_noun_map(final_noun, tag)
                    if tag == "I":
                        insert_attr = final_noun
                    if tag == "U":
                        update_set_attr = final_noun

            elif token_count == 1 and current_token.lower() in utility.Utility.escape_array: # ignores 'select', 'print'
                continue

            elif current_token.lower() in utility.Utility.insert_array:
                tag = "I"
                self.clauses.type_flag["I"] = 1
                self.clauses.type_flag["S"] = 0
                self.clauses.clause_flag["S"] = 0

            elif current_token.lower() in utility.Utility.update_array:
                tag = "U"
                self.clauses.type_flag["U"] = 1
                self.clauses.clause_flag["U"] = 1
                self.clauses.type_flag["S"] = 0
                self.clauses.clause_flag["S"] = 0

            elif current_token.lower() in utility.Utility.delete_array:
                tag = "D"
                self.clauses.clause_flag["D"] = 1
                self.clauses.type_flag["D"] = 1
                self.clauses.type_flag["S"] = 0
                self.clauses.clause_flag["S"] = 0

            elif current_token.lower() in utility.Utility.limit_word_dict.keys():
                limit_flag = 1
                self.clauses.clause_flag["L"] = 1
                number = utility.Utility.limit_word_dict[current_token]
                self.clauses.limit_clause = str(number - 1) + ", " + "1"

            # Ignore the word 'order' e.g. increasing order
            elif self.clauses.clause_flag["O"] == 1 and current_token == "order":
                continue

            # if token belongs to order_by words like increasing, decreasing etc.
            elif current_token in utility.Utility.order_by_dict.keys() and self.clauses.type_flag["S"] == 1:
                # handle reverse alphabetical like words
                if continuous_order_by_flag == 1 and token_count - previous_order_by_count == 1:
                    continue
                else:
                    prev_tag = tag
                    tag = "O"
                    self.clauses.clause_flag["O"] = 1
                    temp_order = utility.Utility.order_by_dict[current_token]
                    previous_order_by_count = token_count
                    continuous_order_by_flag = 1

            # if token is one of the aggregate_of_dict, eg. average
            elif current_token in utility.Utility.aggregate_of_dict.keys():
                # greater than average of .....
                if earlier_token_flag == "first_rel_op":
                    earlier_token_flag = ""
                    final_rel_op = temp_continuous_rel_op
                    temp_continuous_rel_op = ""
                # student average, won't be considered as an aggregate, but a noun.
                if earlier_token_flag == "first_noun":
                    earlier_token_flag = ""
                    final_noun = temp_noun + " " + current_token.lower()
                    self.add_to_noun_map(final_noun, tag)
                    if tag == "I":
                        insert_attr = final_noun
                    if tag == "U":
                        update_set_attr = final_noun
                    temp_noun = ""
                    # maximum of 'student average' which is an attribute
                    if aggregate_flag == 1:
                        clauses.AggregateClause.add_aggr_attr(self.clauses, final_aggr, final_noun, tag)
                        aggregate_flag = 0
                    # each / every student average
                    if group_by == 1:
                        clauses.GroupByClause.add_to_group_by_clause(self.clauses, final_noun, attribute_flag=0)
                        group_by = 0
                    # decreasing order of 'student average'
                    if final_noun != "":
                        temp_attr = final_noun
                    if tag == "O":
                        if final_noun != "":
                            temp_order_attr = final_noun
                    final_noun = ""
                # normal average, count
                else:
                    aggregate_flag = 1
                    earlier_token_flag = ""
                    final_aggr = utility.Utility.aggregate_of_dict[current_token]

            elif current_token in utility.Utility.aggregate_dict.keys():
                # greater than most
                if limit_flag == 0:
                    if earlier_token_flag == "first_rel_op":
                        final_rel_op = temp_continuous_rel_op
                        temp_continuous_rel_op = ""
                    # name minimum
                    elif earlier_token_flag == "first_noun":
                        final_noun = temp_noun
                        self.add_to_noun_map(final_noun, tag)
                        temp_noun = ""
                        if tag == "I":
                            insert_attr = final_noun
                        if tag == "U":
                            update_set_attr = final_noun
                        if aggregate_flag == 1:
                            clauses.AggregateClause.add_aggr_attr(self.clauses, final_aggr, final_noun, tag)
                        if group_by == 1:
                                clauses.GroupByClause.add_to_group_by_clause(self.clauses, final_noun, attribute_flag=0)
                                group_by = 0
                        if tag == "O":
                            if final_noun != "":
                                temp_order_attr = final_noun
                    # for the case 'salary is greater than average of salary'
                    if final_noun != "":
                        temp_attr = final_noun
                    final_noun = ""
                    aggregate_flag = 1
                    earlier_token_flag = ""
                    final_aggr = utility.Utility.aggregate_dict[current_token]
                else:
                    temp_order = utility.Utility.limit_dict[current_token]
                    prev_tag = tag
                    tag = "O"
                    self.clauses.clause_flag["O"] = 1

            elif current_token in utility.Utility.break_words:
                # less than ... (might not be needed)
                if earlier_token_flag == "first_rel_op":
                    final_rel_op = temp_continuous_rel_op
                    earlier_token_flag = ""
                elif constant_flag == "first_const" and final_const == "":
                    constant_flag = 0
                    final_const = temp_continuous_const
                    temp_continuous_const = ""
                    if tag == "I":
                        insert_value = final_const
                    if tag == "U":
                        update_set_value = final_const
                elif earlier_token_flag == "first_noun":
                    earlier_token_flag = ""
                    final_noun = temp_noun
                    self.add_to_noun_map(final_noun, tag)
                    temp_noun = ""
                    if tag == "I":
                        insert_attr = final_noun
                    if tag == "U":
                        update_set_attr = final_noun
                    if group_by == 1:
                        clauses.GroupByClause.add_to_group_by_clause(self.clauses, final_noun, attribute_flag=0)
                        group_by = 0
                    if aggregate_flag == 1:
                        final_aggr_noun = final_noun
                        clauses.AggregateClause.add_aggr_attr(self.clauses, final_aggr, final_aggr_noun, tag)
                        aggregate_flag = 0
                    # increasing order of names with.....
                    if tag == "O":
                        if final_noun != "":
                            temp_order_attr = final_noun
                    if final_noun != "":
                        temp_attr = final_noun
                    final_noun = ""
                # once tag is W, dont touch
                if (tag != "W" and self.clauses.type_flag["S"] == 1) or tag == "U":
                    prev_tag = tag
                    tag = "WT"
                # Comp Sci department WITH salary greater than 80000
                # when with, then set conjunction flag
                if tag == "W" and final_const != "" and temp_attr !="":
                    earlier_token_flag = "conj"

            # In all conditions after this, 2 loops to check earlier_token_flag == 1 or 2 are common
            # earlier_token_flag = "of"
            # if 'of' is encountered, earlier_token_flag = 3, which helps us group two nouns together,
            # eg. name of departments;
            # name and department are put together in a noun
            # earlier_token_flag = "first_rel_op"
            # tells us that the last word was a comparison word (JJR, greater) which won't added to the relational
            # operator list until the next word was examined (eg. equal), so that it becomes
            # 'greater equal' before it is appended
            # earlier_token_flag = "first_noun"
            #   First noun of the noun-pair is found - eg. name od students, when name is found, earlier_token_flag = 1
            #   tells us that the last word was a noun, (names) which won't added to the noun map until the next word is
            #   examined (eg. student), so that they are clubbed together and added to list (name student)
            # tag = 'W'
            #   Handles all the cases if the word is a part of a WHERE clause
            # tag = 'O'
            #   Handles all the cases if the word is a part of a ORDER BY clause

            elif current_token.lower() == "between" and self.clauses.type_flag["S"] == 1:  # if between is in the sentence, signals the BETWEEN clause
                if constant_flag == "first_const" and final_const == "":
                    constant_flag = 0
                    final_const = temp_continuous_const
                    temp_continuous_const = ""
                prev_tag = tag
                tag = "W"
                self.clauses.clause_flag["W"] = 1
                self.clauses.between_flag = 1

            elif current_token == "of" or current_token_tag == "POS":
                if earlier_token_flag == "first_noun":
                    earlier_token_flag = "of"
                if constant_flag == "first_const" and final_const == "":
                    constant_flag = 0
                    final_const = temp_continuous_const
                    temp_continuous_const = ""
                    if tag == "I":
                        insert_value = final_const
                    if tag == "U":
                        update_set_value = final_const

            elif current_token == "equal":
                # Perriridge equal to ....
                if constant_flag == "first_const" and final_const == "":
                    constant_flag = 0
                    final_const = temp_continuous_const
                    temp_continuous_const = ""
                    if tag == "I":
                        insert_value = final_const
                    if tag == "U":
                        update_set_value = final_const
                # greater than and equal .....
                if earlier_token_flag == "first_rel_op":
                    final_rel_op = temp_continuous_rel_op + " " + current_token
                    earlier_token_flag = ""
                # credits equal....
                elif earlier_token_flag == "first_noun":
                    earlier_token_flag = ""
                    final_noun = temp_noun
                    self.add_to_noun_map(final_noun, tag)
                    if tag == "I":
                        insert_attr = final_noun
                    if tag == "U":
                        update_set_attr = final_noun
                    if group_by == 1:
                        clauses.GroupByClause.add_to_group_by_clause(self.clauses, final_noun, attribute_flag=0)
                        group_by = 0
                    if aggregate_flag == 1:
                        final_aggr_noun = final_noun
                        clauses.AggregateClause.add_aggr_attr(self.clauses, final_aggr, final_aggr_noun, tag)
                        aggregate_flag = 0
                    if tag == "O":
                        if final_noun != "":
                            temp_order_attr = final_noun
                    temp_noun = ""

            # Tags 'NN' and 'NNS' cover all nouns
            elif current_token_tag == "NNS" or current_token_tag == "NN":  # Nouns (student, grades)
                if constant_flag == "first_const" and final_const == "":
                    final_const = temp_continuous_const
                    temp_continuous_const = ""
                    if tag == "I":
                        insert_value = final_const
                    if tag == "U":
                        update_set_value = final_const
                # Perryridge branch
                if constant_flag == "first_const" and token_count - previous_constant_count == 1:
                    constant_flag = 0
                    earlier_token_flag = "first_noun"
                    previous_count = token_count
                    temp_noun = current_token.lower()
                    final_noun = ""
                # greater than 'noun' - does not make sense actually
                elif earlier_token_flag == "first_rel_op":
                    earlier_token_flag = ""
                    final_rel_op = temp_continuous_rel_op
                    temp_continuous_rel_op = ""
                # names of departments
                elif earlier_token_flag == "of":
                    # change it
                    earlier_token_flag = ""
                    final_noun = temp_noun + " " + current_token.lower()
                    temp_noun = ""
                    self.add_to_noun_map(final_noun, tag)
                    if group_by == 1:
                        clauses.GroupByClause.add_to_group_by_clause(self.clauses, final_noun, attribute_flag=0)
                        group_by = 0
                    if aggregate_flag == 1:
                        final_aggr_noun = final_noun
                        clauses.AggregateClause.add_aggr_attr(self.clauses, final_aggr, final_aggr_noun, tag)
                        aggregate_flag = 0

                elif earlier_token_flag == "first_noun":
                    # continuous names - student names
                    if token_count - previous_count == 1:
                        final_noun = temp_noun + " " + current_token.lower()
                        self.add_to_noun_map(final_noun, tag)
                        if group_by == 1:
                            clauses.GroupByClause.add_to_group_by_clause(self.clauses, final_noun, attribute_flag=0)
                            group_by = 0
                        if aggregate_flag == 1:
                            final_aggr_noun = final_noun
                            clauses.AggregateClause.add_aggr_attr(self.clauses, final_aggr, final_aggr_noun, tag)
                            aggregate_flag = 0
                        temp_noun = ""
                        earlier_token_flag = ""
                    # course_id and student name
                    else:
                        final_noun = temp_noun
                        self.add_to_noun_map(final_noun, tag)
                        if group_by == 1:
                            clauses.GroupByClause.add_to_group_by_clause(self.clauses, final_noun, attribute_flag=0)
                            group_by = 0
                        if aggregate_flag == 1:
                            final_aggr_noun = final_noun
                            clauses.AggregateClause.add_aggr_attr(self.clauses, final_aggr, final_aggr_noun, tag)
                            aggregate_flag = 0
                        temp_noun = current_token.lower()
                        previous_count = token_count  # course_id and student name
                # normal first noun - department, credits
                else:
                    earlier_token_flag = "first_noun"
                    previous_count = token_count
                    temp_noun = current_token.lower()

                # tag will be "W"
                if tag == "W":
                    # check if the previous word was conjunction, reset the constant_flag
                    # e.g. credits are 90 and name.....
                    if constant_flag == "found_const_conj":
                        #where_count += 1
                        constant_flag = 0

                if tag == "I":
                    if final_noun != "":
                        insert_attr = final_noun

                if tag == "U":
                    if final_noun != "":
                        update_set_attr = final_noun

                if final_noun != "":
                    temp_attr = final_noun

                if tag == "O":
                    if final_noun != "":
                        temp_order_attr = final_noun
                # reset final_noun after it is used for either WHERE or ORDER BY clause
                final_noun = ""

            elif current_token_tag == "CD" or current_token_tag == "NNP" or current_token_tag == "NNPS":  # Constants and Proper Nouns (100, Pranay)
                if earlier_token_flag == "first_rel_op":
                    earlier_token_flag = ""
                    final_rel_op = temp_continuous_rel_op
                    temp_continuous_rel_op = ""
                # department 'Physics'
                elif earlier_token_flag == "first_noun":
                    final_noun = temp_noun
                    self.add_to_noun_map(final_noun, tag)
                    if tag == "I":
                        insert_attr = final_noun
                    if tag == "U":
                        update_set_attr = final_noun
                    if aggregate_flag == 1 :
                        final_aggr_noun = final_noun
                        clauses.AggregateClause.add_aggr_attr(self.clauses, final_aggr, final_aggr_noun, tag)
                        aggregate_flag = 0
                    if group_by == 1:
                        clauses.GroupByClause.add_to_group_by_clause(self.clauses, final_noun, attribute_flag=0)
                        group_by = 0
                    if tag == "O":
                        if final_noun != "":
                            temp_order_attr = final_noun
                    earlier_token_flag = ""
                    temp_noun = ""

                # Comp Science
                if constant_flag == "first_const" and token_count - previous_constant_count == 1 and \
                        current_token_tag == "NNP" or current_token_tag == "NNPS":
                    final_const = temp_continuous_const + " " + current_token
                    if tag == "I":
                        insert_value = final_const
                    if tag == "U":
                        update_set_value = final_const
                elif constant_flag == "first_const" and token_count - previous_constant_count == 1:
                    final_const = temp_continuous_const
                    if tag == "I":
                        insert_value = final_const
                    if tag == "U":
                        update_set_value = final_const
                # if tag is not "W", make "W" when constant is found
                if (len(self.clauses.noun_map) > 0 and tag not in ["W", "U", "I"]) or \
                        (tag == "WT" and prev_tag == "U"):
                    prev_tag = tag
                    tag = "W"
                    self.clauses.clause_flag["W"] = 1
                if len(self.clauses.noun_map) == 0 and current_token_tag == "CD":
                    limit_flag = 1
                    self.clauses.clause_flag["L"] = 1
                    self.clauses.limit_clause = str(current_token)
                if tag == "W":
                    if final_noun != "":
                        temp_attr = final_noun
                        final_noun = ""
                    # if earlier word was conjunction and this word is constant, then use the previous rel_op and attr
                    # eg. score is greater than 90 or 100, use score, >, 90 and score, >, 100
                    if constant_flag == "found_const_conj":
                        if token_count - previous_constant_count == 1:
                            temp_attr = prev_attr
                            final_rel_op = prev_rel_op

                    # if earlier word is rel_op, constant earlier_token_flag = 3, use previous attribute for both
                    # rel_op and constants
                    # score is greater than 90 and less than 150; use score, >, 90 and score, <, 150
                    elif constant_flag == "found_rel_op_const":
                        temp_attr = prev_attr
                temp_continuous_const = current_token
                constant_flag = "first_const"
                previous_constant_count = token_count

            elif current_token_tag == "JJ": # for 10th, 1st etc.
                if utility.Utility.has_numbers(current_token):
                    limit_flag = 1
                    self.clauses.clause_flag["L"] = 1
                    string = re.findall("\d+", current_token)
                    number = int(string[0])
                    self.clauses.limit_clause = str(number - 1) + ", " + "1"

            elif current_token_tag == "JJR":  # Comparison operators (eg. less, more)
                # - dont know why this case is there
                if constant_flag == "first_const" and final_const == "":
                    constant_flag = 0
                    final_const = temp_continuous_const
                    temp_continuous_const = ""
                    if tag == "I":
                        insert_value = final_const
                    if tag == "U":
                        update_set_value = final_const
                elif earlier_token_flag == "first_noun":  # This is when noun is followed by JJR
                    final_noun = temp_noun
                    self.add_to_noun_map(final_noun, tag)
                    if tag == "I":
                        insert_attr = final_noun
                    if tag == "U":
                        update_set_attr = final_noun
                    if aggregate_flag == 1:
                        final_aggr_noun = final_noun
                        clauses.AggregateClause.add_aggr_attr(self.clauses, final_aggr, final_aggr_noun, tag)
                        aggregate_flag = 0
                    if group_by == 1:
                        clauses.GroupByClause.add_to_group_by_clause(self.clauses, final_noun, attribute_flag=0)
                        group_by = 0
                    if tag == "O":
                        if final_noun != "":
                            temp_order_attr = final_noun
                    temp_noun = ""
                if final_noun != "":
                    temp_attr = final_noun
                    final_noun = ""
                # credits are greater than 50 and less than....
                if tag == "WT":
                    # if prev word is conjunction, (............ and less ......)
                    if constant_flag == "found_const_conj":
                        constant_flag = "found_rel_op_const"

                temp_continuous_rel_op = current_token.lower()
                earlier_token_flag = "first_rel_op"

            elif current_token_tag == "VB" or current_token_tag == "VBD" or current_token_tag == "VBG" or \
                            current_token_tag == "VBN" or current_token_tag == "VBP" or current_token_tag == "VBZ":
                self.clauses.verb_list.append(current_token)
                # words like customer named - customer name is a noun
                if earlier_token_flag == "first_noun":
                    final_noun = temp_noun
                    self.add_to_noun_map(final_noun, tag)
                    if tag == "I":
                        insert_attr = final_noun
                    if tag == "U":
                        update_set_attr = final_noun
                    if group_by == 1:
                        clauses.GroupByClause.add_to_group_by_clause(self.clauses, final_noun, attribute_flag=0)
                        group_by = 0
                    if aggregate_flag == 1:
                        final_aggr_noun = final_noun
                        clauses.AggregateClause.add_aggr_attr(self.clauses, final_aggr, final_aggr_noun, tag)
                        aggregate_flag = 0
                    if tag == "O":
                        if final_noun != "":
                            temp_order_attr = final_noun
                    temp_noun = ""
                if constant_flag == "first_const" and final_const == "":
                    constant_flag = 0
                    final_const = temp_continuous_const
                    temp_continuous_const = ""
                    if tag == "I":
                        insert_value = final_const
                    if tag == "U":
                        update_set_value = final_const
                earlier_token_flag = ""

            # if conjunction AND (not an insert query with tag W or WT) or (insert query with tag I) or
            # (update query with tag U - set clause)
            elif current_token_tag == "CC" and (((self.clauses.type_flag["I"] == 0 and (tag == "W" or tag == "WT"))
                                                 or tag == "I" or tag == "U")):
                if earlier_token_flag == "first_rel_op":
                    final_rel_op = temp_continuous_rel_op
                    temp_continuous_rel_op = ""
                # Find the name of student who has the highest credits -AND- credits less than 200
                elif earlier_token_flag == "first_noun":
                    final_noun = temp_noun
                    self.add_to_noun_map(final_noun, tag)
                    if tag == "I":
                        insert_attr = final_noun
                    if tag == "U":
                        update_set_attr = final_noun
                    if aggregate_flag == 1:
                        final_aggr_noun = final_noun
                        if tag == "WT": # aggregate acts as a constant
                            clauses.AggregateClause.add_aggr_attr(self.clauses, final_aggr, final_aggr_noun, tag,
                                                                  "const")
                            aggregate_flag = 0
                            clauses.WhereClauseContent.add_where_clause(self.clauses, where_count, final_aggr_noun,
                                 utility.Utility.rel_op_dict[final_rel_op], final_aggr_noun, conj=current_token.upper(),
                                                                        aggr=final_aggr,constant_flag=0)
                            if tag != "W" and tag != "I" and tag != "U":
                                prev_tag = tag
                                tag = "W"
                            self.check_change_tag(temp_attr, prev_tag)
                            self.check_change_tag(final_aggr_noun, prev_tag)
                            prev_attr = temp_attr
                            prev_rel_op = final_rel_op
                            constant_flag = "found_const_conj"
                            previous_constant_count = token_count
                        else:
                            clauses.AggregateClause.add_aggr_attr(self.clauses, final_aggr, final_aggr_noun, tag)
                            aggregate_flag = 0
                    if group_by == 1:
                        clauses.GroupByClause.add_to_group_by_clause(self.clauses, final_noun, attribute_flag=0)
                        group_by = 0
                    if tag == "O":
                        if final_noun != "":
                            temp_order_attr = final_noun
                    temp_noun = ""

                if final_noun != "":
                    temp_attr = final_noun
                    final_noun = ""
                if self.clauses.between_flag == 1:
                    temp_conj = "between"
                    # places the conjunction 'between' in conjunction attribute of object, recently inserted
                    # place_conjunction_where_clause(prev_attr, "between")
                    self.clauses.between_flag = 0

                else:
                    temp_conj = current_token
                    # places the conjunction 'and, 'or' etc. in conjunction attribute of object, recently inserted
                    # place_conjunction_where_clause(prev_attr, current_token)
                earlier_token_flag = "conj"

                if constant_flag == "first_const" and final_const == "":  # '90 or' case, if 'Computer Science or', already done
                    final_const = temp_continuous_const
                    temp_continuous_const = ""
                    if tag == "I":
                        insert_value = final_const
                    if tag == "U":
                        update_set_value = final_const

                # if prev word is constant, then wait and check if next is constant or rel_op or something else
                # i.e 100 and 90,   100 and less....,   100 and score is....
                if constant_flag == "first_const" and token_count - previous_constant_count == 1:
                    constant_flag = "found_const_conj"
                    previous_constant_count = token_count

            # put in where clause if conjunction or break word has occured
            # find all instructors in Comp Sci department -WITH- salary greater than 80000
            # put when temp_attr and final_const are non-empty
            if tag == "W" and final_const != "" and temp_attr != "" and earlier_token_flag == "conj":
                clauses.WhereClauseContent.add_where_clause(self.clauses, where_count, temp_attr, utility.Utility.rel_op_dict[final_rel_op],
                                                            final_const, temp_conj.upper())
                self.clauses.constant_list.append(final_const)
                self.check_change_tag(temp_attr, prev_tag)
                prev_attr = temp_attr
                prev_rel_op = final_rel_op
                earlier_token_flag = ""
                temp_attr, temp_rel_op, final_rel_op, final_const = "", "", "", ""
                tag = "WT"
            # put in order by clause, when temp_order_attr(credits) and temp_order (ASC) are non empty
            elif tag == "O" and temp_order != "" and temp_order_attr != "" and earlier_token_flag == "":
                clauses.OrderByClause.add_order_clause(self.clauses, temp_order, temp_order_attr)
                temp_order, temp_order_attr = "", ""

            elif tag == "I" and insert_value != "" and insert_attr != "":
                clauses.InsertClause.add_to_insert_clause(self.clauses, insert_attr, insert_value)
                self.clauses.constant_list.append(final_const)
                insert_attr, insert_value, final_const = "", "", ""

            elif self.clauses.type_flag["U"] == 1 and update_set_value != "" and update_set_attr != "":
                clauses.SetClause.add_to_set_clause(self.clauses, update_set_attr, update_set_value)
                self.clauses.constant_list.append(final_const)
                update_set_attr, update_set_value, final_const = "", "", ""
        # If anything is remaining in the variable 'temp', then append to noun_map
        if tag == "I":
            if final_const == "" and constant_flag == "first_const":
                insert_value = temp_continuous_const
                self.clauses.constant_list.append(insert_value)
            if earlier_token_flag == "first_noun":
                final_noun = temp_noun
                self.add_to_noun_map(final_noun, tag)
                insert_attr = final_noun
            if insert_attr != "" and insert_value != "":
                clauses.InsertClause.add_to_insert_clause(self.clauses, insert_attr, insert_value)

        elif tag == "U":
            if final_const == "" and constant_flag == "first_const":
                update_set_value = temp_continuous_const
                self.clauses.constant_list.append(update_set_value)
            if earlier_token_flag == "first_noun":
                final_noun = temp_noun
                self.add_to_noun_map(final_noun, tag)
                update_set_attr = final_noun
            if insert_attr != "" and insert_value != "":
                clauses.SetClause.add_to_set_clause(self.clauses, update_set_attr, update_set_value)

        elif tag == "O" and temp_order_attr == "" and temp_order != "" and earlier_token_flag == "":
            self.clauses.order_default_list.append(temp_order)

        # if last word is a single word noun
        elif tag == "O" and temp_order_attr == "" and temp_order != "" and earlier_token_flag == "first_noun":
            final_noun = temp_noun
            self.add_to_noun_map(final_noun, tag)
            temp_order_attr = final_noun
            clauses.OrderByClause.add_order_clause(self.clauses, temp_order, temp_order_attr)

        # final word is noun and aggregate acts as constant
        # Find the instructor id whose salary is greater than average salary of instructor
        elif tag == "WT" and earlier_token_flag == "first_noun" and aggregate_flag == 1:
            final_noun = temp_noun
            self.add_to_noun_map(final_noun, tag)
            if aggregate_flag == 1:
                final_aggr_noun = final_noun
                clauses.AggregateClause.add_aggr_attr(self.clauses, final_aggr, final_aggr_noun, tag, "const")
                clauses.WhereClauseContent.add_where_clause(self.clauses, where_count, final_aggr_noun,
                        utility.Utility.rel_op_dict[final_rel_op], final_aggr_noun, aggr=final_aggr, constant_flag=0)
                self.check_change_tag(temp_attr, "WT")
                self.check_change_tag(final_aggr_noun, "WT")

        elif tag == "WT" and earlier_token_flag == "" and final_const == "":
            if self.noun_present_in_aggregate(temp_attr):
                final_noun = temp_attr
                clauses.WhereClauseContent.add_where_clause(self.clauses, where_count, final_noun,
                                                            utility.Utility.rel_op_dict[final_rel_op],
                                                            final_noun, aggr=final_aggr, constant_flag=0)
                self.change_type_in_aggregate(final_noun, final_aggr)
                self.check_change_tag(temp_attr, "WT")
                self.check_change_tag(final_noun, "WT")

        # final word is noun  - Pranay is the name
        elif tag == "W" and earlier_token_flag != "" and final_const != "":
            final_noun = temp_noun
            self.add_to_noun_map(final_noun, tag)
            if aggregate_flag == 1:
                clauses.AggregateClause.add_aggr_attr(self.clauses, final_aggr, final_noun, tag)
            temp_attr = final_noun
            clauses.WhereClauseContent.add_where_clause(self.clauses, where_count, temp_attr,
                                                        utility.Utility.rel_op_dict[final_rel_op], final_const)
            self.clauses.constant_list.append(final_const)
            self.check_change_tag(temp_attr, prev_tag)

        # final word is constant - salary is 80000
        elif tag == "W" and earlier_token_flag == "" and constant_flag == "first_const" and temp_attr != "":
            if final_const == "":
                final_const = temp_continuous_const
            clauses.WhereClauseContent.add_where_clause(self.clauses, where_count, temp_attr,
                                                        utility.Utility.rel_op_dict[final_rel_op], final_const)
            self.clauses.constant_list.append(final_const)
            self.check_change_tag(temp_attr, prev_tag)

        # Perryridge branch name
        elif tag == "W" and earlier_token_flag == "" and final_const != "":
            clauses.WhereClauseContent.add_where_clause(self.clauses, where_count, temp_attr,
                                                        utility.Utility.rel_op_dict[final_rel_op], final_const)
            self.clauses.constant_list.append(final_const)
            self.check_change_tag(temp_attr, prev_tag)

        elif earlier_token_flag != "":
            final_noun = temp_noun
            self.add_to_noun_map(final_noun, tag)

        if constant_flag == "first_const":
            self.clauses.constant_list.append(temp_continuous_const)

        # if group by final_noun is not yet found - please check this again
        if earlier_token_flag != "" and group_by == 1:
            clauses.GroupByClause.add_to_group_by_clause(self.clauses, final_noun, attribute_flag=0)

    def finalize_clauses(self):
        clauses.WhereClauseContent.get_having_clause(self.clauses)
        clauses.GroupByClause.get_group_clauses(self.clauses)
