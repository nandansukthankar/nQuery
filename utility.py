from nltk.tag.stanford import StanfordPOSTagger
import os
from difflib import SequenceMatcher
import nltk
from nltk.stem import PorterStemmer, WordNetLemmatizer


class Utility:
    # Words in a natural language which tell us that the information that follows, belongs to the WHERE clause
    break_words = ["in", "for", "at", "whose", "having", "where", "have", "who", "that", "with", "by", "under", "from"]

    # Dictionary mapping relational operators with their algebraic signs
    rel_op_dict = {"greater": ">", "more": ">", "less": "<", "greater equal": ">=", "less equal": "<=", "equal": "=",
                   "": "=", "except": "!=", "not": "!="}

    order_by_dict = {"ordered": "ASC", "sorted": "ASC", "alphabetical": "ASC", "alphabetically": "ASC",
                     "increasing": "ASC", "decreasing": "DESC", "ascending": "ASC", "descending": "DESC",
                     "reverse": "DESC", "alphabetic": "ASC"}

    aggregate_of_dict = {"number": "COUNT", "count": "COUNT", "total": "SUM", "sum": "SUM", "average": "AVG",
                         "mean": "AVG"}

    aggregate_dict = {"maximum": "MAX", "highest": "MAX", "minimum": "MIN", "most": "MAX", "least": "MIN",
                      "lowest": "MIN", "largest": "MAX", "smallest": "MIN"}

    limit_dict = {"maximum": "DESC", "highest": "DESC", "minimum": "ASC", "most": "DESC", "least": "ASC",
                  "lowest": "ASC", "largest": "DESC", "smallest": "ASC"}

    limit_word_dict = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7,
                       "eighth": 8, "ninth": 9, "tenth": 10}

    escape_array = ["find", "select", "publish", "print", "who", "where", "which", "what", "give", "list", "i", "we",
                    "show"]

    insert_array = ["insert", "put"]

    update_array = ["update", "edit", "set", "change"]

    delete_array = ["delete", "remove"]

    @staticmethod
    def has_numbers(string):
        return any(char.isdigit() for char in string)

    @staticmethod
    def parse_string_to_float(string):
        string_temp = string.replace(",", "")
        return float(string_temp)

    # Tokenize the string
    @staticmethod
    def tokenize(natural_lang_query):
        remove_char = ["'", "$", "\"", "`"]
        for c in remove_char:
            natural_lang_query = natural_lang_query.replace(c, "")
        tokens = nltk.word_tokenize(natural_lang_query)
        return tokens

    # Tag the tokens generated, using NLTK's POS_TAG function
    @staticmethod
    def tag_nltk(tokens):
        tagged = nltk.pos_tag(tokens)
        return tagged

    @staticmethod
    def tag(tokens):
        #java_path = "C:/Program Files/Java/jdk1.8.0_31/bin/java.exe"
        #os.environ['JAVAHOME'] = java_path
        special_symbols_array = ["the", "a", "an"]
        english_postagger = StanfordPOSTagger(
            'tagger/english-bidirectional-distsim.tagger',
            'tagger/stanford-postagger.jar')
        token_tag_array = english_postagger.tag(tokens)
        for element in token_tag_array:
            if element[0].lower() in special_symbols_array:
                token_tag_array.remove(element)
        return token_tag_array
    # Function to stem the string using PorterStemmer Module in Python
    @staticmethod
    def stem(token_string):
        stemmer = PorterStemmer()
        return  stemmer.stem(token_string)

    @staticmethod
    def lemmatize(token_string):
        lemmatiser = WordNetLemmatizer()
        return lemmatiser.lemmatize(token_string, 'v')

    # If attribute belongs to a table, its name can be either the attribute itself or a combination of the
    # attribute and table_name, for example, if table 'student' has an attribute to describe his name, then it can be
    # one out of 'name' or combination of 'student' and 'name', i.e 'stud_name'
    # para1 - noun or part of combined noun
    # para2 - attribute of table
    # para3 - perfect match / substring match flag
    # para4 - both match / none flag
    # returns true / false
    @staticmethod
    def check_substring_attr(noun_para, attr_para, substring_perfect_flag, both_match_flag=None):
        attr_para = attr_para.lower()

        # If perfect_match, then the attribute and string from NL statement have to match perfectly (attr-name, noun-name)
        if substring_perfect_flag == "perfect_match":
            if noun_para == Utility.stem(attr_para):
                return True

        else:  # if substring_perfect_flag is substring match, first split attribute by _ ,
            split_attr = attr_para.split('_')

            # if there is no _ in attr (name or studName)
            if len(split_attr) == 1:

                # if both_match_flag is both match, i.e. attribute is made of combined noun and no _ (studName)
                if both_match_flag == "both_match":
                    noun_split_array = noun_para.split()  # splitting combined noun by space (name, student)
                    # match for each part of noun (name, student) as substring in attribute (studName)
                    # if even one part is not substring, return false
                    for element in noun_split_array:

                        element = Utility.stem(element)
                        match = SequenceMatcher(None, element, attr_para).find_longest_match(0, len(element), 0,
                                                                                             len(attr_para))
                        if match.size < 2 or match.a != 0:  # minimum substring match of length 2 required
                            return False
                    return True

                else:  # if both_match_flag is none (not checking for all parts of combine noun) i.e. noun - name
                    # check for noun as substring in attr with min length 4
                    match = SequenceMatcher(None, noun_para, split_attr[0]).find_longest_match(0, len(noun_para), 0,
                                                                                               len(split_attr[0]))

                    # print("noun_para, attr_para",noun_para, attr_para)
                    if match.size >= 4 and match.a == 0:  # match.a == 0 because we want substring that is from index 0
                        return True

            else:  # if there is _ in attr (stud_name)

                # If _ is present, BOTH sides of the underscore should completely match with the noun element
                # e.g. attr - stud_name, noun - name student, then 'stud' is completely present in 'name student'
                # and 'name' is completely present in 'name student'
                if both_match_flag == "both_match":
                    for element in split_attr:
                        element = Utility.stem(element)
                        match = SequenceMatcher(None, noun_para, element).find_longest_match(0, len(noun_para), 0,
                                                                                             len(element))

                        if match.size != len(element) or (
                                match.a != 0 and noun_para[match.a - 1] != ' '):  # do something
                            return False
                    return True

                # If _ is present but not both match, EITHER side of the underscore should completely match with the noun element
                else:
                    for element in split_attr:
                        element = Utility.stem(element)
                        match = SequenceMatcher(None, noun_para, element).find_longest_match(0, len(noun_para), 0,
                                                                                             len(element))
                        if match.size == len(element) and match.size >= 2:  # do something
                            return True
                    return False
        return False

    # Accepts two strings as input
    # string1 - noun/verb
    # string2 - table name
    # flag - whether string1 is noun or verb
    # Output - [boolean, matched substring] where boolean is True if match occurs, and the matched substring is returned
    # -------------------------------------------
    """
    ALGO:
    Table name can be with or without _
    So first split table name by _
    if verb is passed
        lemmatize the verb to get in present tense
        lemmatize every split token of table name to get in present tense
    if no _ table name
        match for longest substring betn table name and string1 (noun/verb) for min length 4
        if found, return TRUE and matched substring
        else, return FALSE
    else if _ in table name
        for ANY token of split table name
            if atleast one token is COMPLETELY present in noun/verb, return TRUE and matched substring
        if no token satisfies above cond, return FALSE
    """

    # -------------------------------------------

    # REMAINING: SUBSTRING AT START OF NOUN
    @staticmethod
    def check_substring_table(noun_verb_para, table_name_para, noun_verb_flag=None):
        split_table_name = table_name_para.split('_')  # Split using '_'

        if noun_verb_flag == "verb":
            noun_verb_para = Utility.lemmatize(noun_verb_para)
            for i in range(0, len(split_table_name)):
                split_table_name[i] = Utility.lemmatize(split_table_name[i])

        if len(split_table_name) == 1:
            match = SequenceMatcher(None, noun_verb_para, split_table_name[0]).find_longest_match(0, len(noun_verb_para), 0,
                                                                                  len(split_table_name[0]))
            # If no underscore, the minimum match for the return value to be True is set to be 4
            # If table name is 'classroom' and the string from the NL statement is 'room', match is 'room' (len=4)
            if match.size >= 4 and (match.a == 0 or noun_verb_para[match.a - 1] == ' '):  # do something
                return True, noun_verb_para[match.a: match.a + match.size]

        else:
            # If table_name contains an underscore
            for element in split_table_name:
                match = SequenceMatcher(None, noun_verb_para, element).find_longest_match(0, len(noun_verb_para), 0, len(element))
                # If underscore is present, EITHER side of the underscore should completely match with the noun element
                # If table name is 'stud_name' and the string from the NL statement is 'student', ('stud' and 'student')

                if match.size == len(element) and (match.a == 0 or noun_verb_para[match.a - 1] == ' '):
                    return True, noun_verb_para[match.a: match.a + match.size]
        return False, ""

    @staticmethod
    def convert_proper_noun_to_upper(token_tag_array):
        tagged_tokens = list()
        for i in range(0, len(token_tag_array)):
            token_element = list(token_tag_array[i])
            if token_element[0][0] == "'" and len(token_element[0]) > 1 and token_element[0][1] != "s":  # avoids student's and 'Student'
                token_element[0] = token_element[0][1:len(token_element[0])].upper()
                token_element[1] = "NNP"
            elif token_element[0][0].isupper():
                token_element[1] = "NNP"
            tagged_tokens.append(token_element)
        return tagged_tokens
