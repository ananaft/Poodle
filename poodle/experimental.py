from config import *
from core import *
# import context
from pprint import pprint

# def create_exam(exam, filename='import.xml'):
#     """
#     Creates an xml file out of questions within the database. While using this
#     function the user will be asked whether they want to use automatic or manual
#     creation mode. In automatic mode a file which contains questions' names
#     separated by whitespace is used to automatically generate the xml file. In
#     manual mode the user will type in each question one by one.

#     After the xml file is created, an exam document will be added to the EXAMS
#     collection and all corresponding question documents will be modified within
#     the QUESTIONS collection.

#     Arguments:
#     ----------
#     exam (str):
#       Name of the exam within Moodle/Poodle.
#     filename (str):
#       Name of the output xml file.

#     ------------------------------
#     Dependencies: config, core, re
#     """

#     # Write XML
#     questionlist, info = create_xml(exam, filename)

#     # Write solution dofile
#     create_solution(f'{BASE_PATH}/exams/{exam}/solution.do',
#                     f'{BASE_PATH}/solutions', questionlist)

#     # Update database
#     EXAMS.insert_one({
#         'name': exam,
#         'points_max': info[2],
#         'time_est': info[0],
#         'difficulty_avg': info[1],
#         'questions': questionlist
#     })
#     for q in questionlist:
#         QUESTIONS.find_one_and_update(
#             {'name': q}, {'$set': {f'in_exams.{exam}': np.nan}}
#         )
#     print('Database updated.')


# def create_testexam(exam, filename='import.xml', solution=False):
#     """
#     This function is very similar to 'create_exam()' and is intended for
#     experimenting with its features. It will not create any entries within the
#     database upon creation of the exam. The 'solution' argument decides whether
#     a dofile will be created or not. Apart from this, 'create_testexam()'
#     functions exactly like 'create_exam()'.

#     Arguments:
#     ----------
#     exam (str):
#       Name of the exam within Moodle/Poodle.
#     filename (str):
#       Name of the output xml file.
#     solution (bool):
#       If set to True, function will write a solution dofile.

#     ------------------------------
#     Dependencies: config, core, re
#     """

#     # Write XML
#     questionlist, info = create_xml(exam, filename)

#     if solution:
#         create_solution(f'{BASE_PATH}/exams/{exam}/solution.do',
#                         f'{BASE_PATH}/solutions', questionlist)

#     print('Test exam successfully created.')


def test_question(question, exam='Poodle-Test', filename='import.xml'):
    # Create directory
    try:
        os.mkdir(f'{BASE_PATH}/exams/{exam}')
    except FileExistsError:
        pass
    # Possibly adjust filename
    if filename[-4:] != '.xml':
        filename += '.xml'
    # Don't overwrite existing files
    version = 0
    pattern = re.compile(r'^.+?(?=[-0-9]*\.xml)')
    while filename in os.listdir(f'{BASE_PATH}/exams/{exam}'):
        version += 1
        m = re.match(pattern, filename)
        filename = m.group() + f'-{version}.xml'

    # Create XML base document
    xml_string = (
        '<?xml version="1.0"?>\n'
        '<quiz>\n\n'
        '<!-- question: 0  -->\n'
        '  <question type="category">\n'
        '    <category>\n'
        f'      <text>$course$/top/{exam}</text>\n'
        '    </category>\n'
        '    <info format="moodle_auto_format">\n'
        '      <text></text>\n'
        '    </info>\n'
        '    <idnumber></idnumber>\n'
        '  </question>\n\n'
        '</quiz>'
    )
    root = ET.XML(xml_string)

    questionlist = [question]
    pprint(QUESTIONS.find_one({'name': question}))

    # Append XML
    for q in questionlist:
        q_dict = QUESTIONS.find_one({'name': q})
        q_el = eval((
            f'{q_dict["moodle_type"].capitalize()}'
            f'Question(attrib={{"type": "{q_dict["moodle_type"]}"}})'
        ))
        q_el.set_defaults(q_dict)
        q_el.set_additional(q_dict)
        root.append(q_el)

    with open(f'{BASE_PATH}/exams/{exam}/{filename}', 'w') as wf:
        wf.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        wf.write(ET.tostring(root, pretty_print=True).decode('utf-8'))


def test_exam_creation(qfile):
    with open(qfile, 'r') as rf:
        for line in rf:
            if line[-3:-1] != '00':
                test_question(line[:-1])
