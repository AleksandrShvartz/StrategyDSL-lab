import os

import logging

from dsl.parser import Grammar

logger = logging.getLogger('example_logger')
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
DSL_EXTENSION = '.str'


def parse_file(input_name: str) -> str | None:
    if input_name.endswith('.py'):
        return input_name
    if not input_name.endswith(DSL_EXTENSION):
        logger.info(f'File {input_name} has incorrect extension')
        return None
    if not os.path.isfile(input_name):
        logger.error(f'File {input_name} does not exist')
    file = open(input_name, "r")
    lines = file.readlines()
    # print whole file to a string with removing comments
    is_commented = False
    data = ''
    gr = Grammar()
    # clean from comments
    for line in lines:
        line = line.strip()
        ind_line_commented = len(line)
        for i, c in enumerate(line):
            if c == '@':
                is_commented = not is_commented
            if c == '#' and not is_commented and ind_line_commented == len(line):
                ind_line_commented = i
            if not (is_commented or ind_line_commented != len(line)):
                data += c
    code = gr.parse(data)
    with open(input_name[:len(input_name) - len(DSL_EXTENSION)] + '.py', 'w') as f:
        f.write(code)
    # close file
    file.close()
