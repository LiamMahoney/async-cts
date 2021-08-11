import configparser, os, sys

def parse_tuple(input):
    """
    Parses the config value into a tuple.
    :param string input: value from config
    :returns tuple
    """
    return tuple(x.strip().replace("'", "").replace("\"", "") for x in input[1:-1].split(','))

config = configparser.ConfigParser(converters={'tuple': parse_tuple})
config.read(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'app.config'))