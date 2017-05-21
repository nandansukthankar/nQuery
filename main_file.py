import database
import overall_details
import sql_query_details


def compare():
    base_op = open("base_output.txt", "r")
    op = open("output.txt", "r")
    log = open("log.txt", "w")

    line1 = next(base_op)
    line2 = next(op)

    count = 1

    while line1 and line2:
        if line1 != line2:
            log.write("Query %d\n" % count)
            print("Query ", count)
        count += 1
        line1 = next(base_op)
        line2 = next(op)

    base_op.close()
    op.close()
    log.close()


op_file = open("output.txt", "w")

db = database.Database("localhost", "nandans16", "1234", "bank")
db.connect()

overall_details = overall_details.OverallDetails(db)
overall_details.collect_details()

count = 1
with open('ip1.txt') as fp:
    for line in fp:
        natural_lang_query = line.strip('\n')
        print("%d %s" % (count, natural_lang_query))

        sql_query_details_obj = sql_query_details.SQLQueryDetails(db, overall_details)

        clauses = sql_query_details_obj.collect_query_details(natural_lang_query)

        [query, type_query] = clauses.create_query()
        # use the type variable wherever you want
        print("\n-----------")
        print("Final query: ", query)
        print("-----------\n")
        op_file.write(query + "\n")
        count += 1

op_file.close()

# compare()



