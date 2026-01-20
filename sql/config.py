from configparser import ConfigParser
import os

def config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    ini_path = os.path.join(base_dir, filename)

    if not parser.read(ini_path):
        raise FileNotFoundError(f"Config file not found: {ini_path}")

    if not parser.has_section(section):
        raise Exception(f"Section {section} not found in {ini_path}")

    return dict(parser.items(section))
