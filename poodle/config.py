import pymongo
import os
import sys

# MongoDB
CLIENT = pymongo.MongoClient()
DB = eval(f'CLIENT.{sys.argv[-1]}')
QUESTIONS = DB.questions
EXAMS = DB.exams

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Exams
SHUFFLE = True
RANDOM_ARR_SIZE = 100

Q_CATEGORIES = {'stata': ['10dataman', '20doc', '30funk', '41con', '42con', '51cr', '52cr', '60lab', '70miss', '81reg', '82reg', '90graph'], 'methoden1b': ['01basicskn', '01basicsun', '01basicsap', '02smallkvarskn', '02smallkvarsun', '02smallkvarsap', '03largekvarskn', '03largekvarsun', '03largekvarsap', '04graphskn', '04graphsun', '04graphsap', '05simpleregkn', '05simpleregun', '05simpleregap', '06probkn', '06probun', '06probap', '07rvarkn', '07rvarun', '07rvarap', '08estkn', '08estun', '08estap', '09testkn', '09testun', '09testap', '99otherkn', '99otherun', '99otherap', '10technical'], 'test': ['10dataman', '20doc', '30funk', '41con', '42con', '51cr', '52cr', '60lab', '70miss', '81reg', '82reg', '90graph'], 'methoden2': ['011conceptkn', '012conceptun', '013conceptap', '021dagkn', '022dagun', '023dagap', '031tabkn', '032tabun', '033tabap', '041anovakn', '042anovaun', '043anovaap', '051regintrokn', '052regintroun', '053regintroap', '061regadvancedkn', '062regadvancedun', '063regadvancedap', '071regcausalkn', '072regcausalun', '073regcausalap', '081regdiagkn', '082regdiagun', '083regdiagap', '091binarykn', '092binaryun', '093binaryap', '101teffectskn', '102teffectsun', '103teffectsap', '991otherkn', '992otherun', '993otherap', '999technical'], 'methoden': 'quit()', 'methoden1': 'methoden1b'}
