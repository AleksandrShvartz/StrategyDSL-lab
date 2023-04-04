import logging
import os
from pathlib import Path

logger = logging.getLogger("example_logger")
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
DSL_EXTENSION = ".str"
MODULES_DIR_NAME = "dsl/modules"
modules = {}


def load_modules():
    content = os.listdir(MODULES_DIR_NAME)
    for file in content:
        if os.path.isfile(os.path.join(MODULES_DIR_NAME, file)) and file.endswith(
            ".py"
        ):
            name = file[: len(file) - 3]
            modules[name] = exec()


def parse_file(input_name: Path) -> Path | None:
    if input_name.name.endswith(".py"):
        return input_name
    if not input_name.name.endswith(DSL_EXTENSION):
        logger.info(f"File {input_name} has incorrect extension")
        return None
    if not os.path.isfile(input_name):
        logger.error(f"File {input_name} does not exist")
    file = open(input_name, "r")
    lines = file.readlines()
    # print whole file to a string with removing comments
    is_commented = False
    data = ""
    # gr = Grammar()
    # clean from comments
    for line in lines:
        line = line.strip()
        ind_line_commented = len(line)
        for i, c in enumerate(line):
            if c == "@":
                is_commented = not is_commented
            if c == "#" and not is_commented and ind_line_commented == len(line):
                ind_line_commented = i
            if not (is_commented or ind_line_commented != len(line)):
                data += c
    # code = gr.parse(data)
    code = simple_transform(data)
    new_file_name = input_name[: len(input_name) - len(DSL_EXTENSION)] + ".py"
    with open(new_file_name, "w") as f:
        f.write(code)
    # close file
    file.close()
    return new_file_name


def simple_transform(code="RETURN 0"):
    python_code = "import numpy as np\n"
    code = code.replace("\n", " \n ")
    code = code.replace("{", " {")
    code = code.replace("}", " }")
    tokens = code.split(" ")
    # print(code)
    # print(tokens)
    indent = 0
    prefix = 0
    if_flag = 0
    else_flag = 0
    for_flag = 0
    for ind, token in enumerate(tokens):
        if token == "":
            continue
        if token == "\n":
            python_code += "\n" + " " * (indent * 4)
            continue
        if token == "{":
            indent += 1
            prefix += 1
            if if_flag > 0:
                if_flag -= 1
                python_code += " : "
                continue
            if else_flag > 0:
                else_flag -= 1
                python_code += " : "
                continue
            if for_flag > 0:
                for_flag -= 1
                python_code += " : "
                continue

            continue
        if token == "}":
            indent -= 1
            prefix -= 1
            if indent < 0 or prefix < 0:
                logger.error(f"Wrong curly brackets")
                return
            continue
        if token == "IF":
            python_code += "if "
            if_flag += 1
            continue
        if token == "ELSE":
            python_code += "else"
            else_flag += 1
            continue
        if token == "FOREACH":
            python_code += "for "
            for_flag += 1
            continue
        if token == "IN":
            python_code += "in "
            continue
        if token == "NUM" or token == "BOOL":
            continue
        if token == "SET":
            if ind == len(tokens) - 1:
                logger.error(f"Wrong set declaration")
                return
            name = tokens[ind + 1]
            python_code += name + " = np.array([])\n"
            continue
        if token == "POW":
            python_code += "** "
            continue
        if token == "DIV":
            python_code += "// "
            continue
        if token == "MOD":
            python_code += "% "
            continue
        if token == "T":
            python_code += "True "
            continue
        if token == "F":
            python_code += "False "
            continue
        if token in {"NOT", "AND", "OR}"}:
            python_code += token.lower() + " "
            continue
        if token == "|=":
            if ind == 0:
                logger.error(f"Wrong {token} ")
                return
            name = tokens[ind - 1]
            python_code += "= " + name + " or "
            continue
        if token == "&=":
            if ind == 0:
                logger.error(f"Wrong {token} ")
                return
            name = tokens[ind - 1]
            python_code += "= " + name + " and "
            continue
        if token.startswith("RANGE"):
            python_code += token.lower() + " "
            continue
        if token == "RETURN":
            python_code += "return "
            continue
        if token.startswith("GET("):
            index = token[4:-1]
            python_code += f"state[{index}]"
            continue
        python_code += token + " "
    return python_code
