import argparse
import os
import subprocess
import toml

# function for initlizing the proj
def init_project(args):
    """Initialize a new project by creating duck.toml, main.py, and tests/ directory."""
    if os.path.exists('duck.toml'):
        print("duck.toml already exists. Aborting.")
        return
    config = {
        'meta': {
            'name': 'My Project',
            'version': '0.1.0',
            'author': '',
            'description': ''
        },
        'dependencies': {},
        'project': {
            'main': 'main.py',
            'tests': 'tests/'
        }
    }
    with open('duck.toml', 'w') as f:
        toml.dump(config, f)
    if not os.path.exists('main.py'):
        with open('main.py', 'w') as f:
            f.write('# Main program\n')
    if not os.path.exists('tests'):
        os.makedirs('tests')
    print("Initialized duck.toml, main.py, and tests/ directory")

# runniung main prg
def run_main(args):
    if not os.path.exists('duck.toml'):
        print("duck.toml not found. Run 'duck init' first.")
        return
    config = toml.load('duck.toml')
    main_file = config.get('project', {}).get('main', 'main.py')
    if not os.path.exists(main_file):
        print(f"{main_file} not found.")
        return
    subprocess.run(['python', main_file])

# Function to run tests
def run_tests(args):
    """Run all tests in the tests dir"""
    if not os.path.exists('duck.toml'):
        print("duck.toml not found. Run 'duck init' first.")
        return
    config = toml.load('duck.toml')
    test_dir = config.get('project', {}).get('tests', 'tests/')
    if not os.path.exists(test_dir):
        print(f"{test_dir} not found.")
        return
    subprocess.run(['pytest', test_dir])

# Function to set configuration values
def set_config(key_value):
    """Set a key-value pair in duck.toml, supporting nested keys."""
    if not os.path.exists('duck.toml'):
        print("duck.toml not found. Run 'duck init' first.")
        return
    try:
        key, value = key_value.split('=', 1)
    except ValueError:
        print("Invalid format. Use key=value")
        return
    config = toml.load('duck.toml')
    keys = key.split('.')
    current = config
    for k in keys[:-1]:
        current = current.setdefault(k, {})
    current[keys[-1]] = value
    with open('duck.toml', 'w') as f:
        toml.dump(config, f)
    print(f"Set {key} to {value}")

# CLI parser goes here
parser = argparse.ArgumentParser(description="duck: A Python Project Management Tool")
subparsers = parser.add_subparsers()

# for 'init'
init_parser = subparsers.add_parser('init', help="Initialize a new project")
init_parser.set_defaults(func=init_project)

# for 'quack'
quack_parser = subparsers.add_parser('quack', help="Run the main program")
quack_parser.set_defaults(func=run_main)

# for 'test'
test_parser = subparsers.add_parser('test', help="Run tests")
test_parser.set_defaults(func=run_tests)

#  for 'set'
set_parser = subparsers.add_parser('set', help="Set a configuration value")
set_parser.add_argument('key_value', help="Key-value pair, e.g., meta.author=ash")
set_parser.set_defaults(func=lambda args: set_config(args.key_value))

args = parser.parse_args()
if hasattr(args, 'func'):
    args.func(args)
else:
    parser.print_help()