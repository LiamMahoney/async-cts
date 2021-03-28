import argparse, os, shutil
from jinja2 import Template

def main():
    parser = argparse.ArgumentParser(description='command line utilities for the resilient_async_cts library')
    sub_parser = parser.add_subparsers()

    codegen_parser = sub_parser.add_parser('codegen', help='generate boilerplate project to speed up development of a cts')
    codegen_parser.add_argument('-n', '--name', help='name of the CTS', required=True)
    codegen_parser.add_argument('-o', '--output', help='directory to output template (default: current working directory)', default=None)

    args = parser.parse_args()
    codegen(str_to_pythonic(args.name), args.output)

def codegen(name, output):
    """
    Generates the CTS project directory and boilerplate files.

    :param string name: the name of the CTS
    :param string output: the location to generate the CTS
    """
    print('Generating boilerplate code.')
    cts_dir = None

    try:
        # making the top level dir
        cts_dir = make_cts_directory(name, output)

        populate_dir(cts_dir, os.path.join(os.path.dirname(__file__), "template"), name=name)
    except Exception as e:
        print('Failed to generate boilerplate code. Cleaning up any partially built directories.')
        if (cts_dir) and os.path.exists(cts_dir):
            # cleaning up partially built dir
            shutil.rmtree(cts_dir)

    finally:
        if (cts_dir and os.path.exists(cts_dir)):
            print(f'CTS boilerplate can be found at {cts_dir}')

        print('Execution complete. Thanks for using resilient_async_cts')

def str_to_pythonic(token):
    """
    Replaces spaces with underscores and lowercases the token.

    :param string token: the string to lower case and replace spaces with '_'
    """
    return token.lower().replace(" ", "_")

def make_cts_directory(name, output):
    """
    Creates the directory for the CTS.

    :param string name: the name of the CTS
    :param string output: the location to generate the CTS
    :returns string the path to the directory created
    """
    if (output):
        if (os.path.exists(output)):
            os.mkdir(os.path.join(output, name))
            return os.path.join(output, name)
        else:
            print(f'Directory {output} doesn\'t exist, writing to cwd instead')

    os.mkdir(os.path.join(os.getcwd(), name))
    return os.path.join(os.getcwd(), name)

def populate_dir(cts_dir, template_dir, **kwargs):
    """
    Populates a directory with the cts boilerplate project files / structure.

    :param string cts_dir: the path of the CTS directory - the path to write to
    :param string template_dir: the path of template / the current level of the template
    """
    # contents of the current level of the template directory
    dir_contents = os.listdir(template_dir)

    # populating the dir with the template
    for template_obj in dir_contents:
        if (os.path.isfile(os.path.join(template_dir, template_obj))):
            make_file(template_dir, template_obj, cts_dir, **kwargs)

        elif (os.path.isdir(os.path.join(template_dir, template_obj))):
            os.mkdir(os.path.join(cts_dir, template_obj))
            # recurisve call for next level of template dir
            populate_dir(os.path.join(cts_dir, template_obj), os.path.join(template_dir, template_obj), **kwargs) 

        else:
            raise Exception('Unkown object in template directory.')

def make_file(template_file_path, template_file_name, cts_path, **kwargs):
    """
    Generates the file in the CTS directory. Populates the jinja template when
    neccessary.

    :param string template_file_path: the path to the template file to make
    :param string cts_path: the cts_path to the cts directory
    :param dict kwargs: values to pass into jinja template
    """
    template = Template(open(os.path.join(template_file_path, template_file_name)).read())
    rendered_template = template.render(**kwargs)

    file_name = template_file_name.replace(".jinja2", "")

    with open(os.path.join(cts_path, file_name), 'w') as file:
        file.write(rendered_template)