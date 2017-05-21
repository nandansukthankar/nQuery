from nltk.tag.stanford import StanfordPOSTagger
import os
java_path = "C:/Program Files/Java/jdk1.8.0_31/bin/java.exe"
os.environ['JAVAHOME'] = java_path


english_postagger = StanfordPOSTagger('D:/BtechProject/stanford-postagger/models/english-bidirectional-distsim.tagger' ,
                                   'D:/BtechProject/stanford-postagger/stanford-postagger.jar')

sentence = "NANDAN SUKTHANKAR PRANAY SANKET DESHMUKH"
print(english_postagger.tag(sentence.split()))
#op_file = open("output.txt", "w")
"""
with open('student_corpus.txt') as fp:
    for line in fp:
        sentence = line.strip('\n')
        token_array = english_postagger.tag(sentence.split())
        op_file.write("\n".join((str(elem) for elem in token_array)))
        print(sentence)
"""
#ct = CRFTagger()
#print(ct.tag(text.split()))
