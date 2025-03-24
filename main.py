#! usr/bin/python3.11
import click, toml, os, shutil
import sys, subprocess, colorama


# better colors for terminal
colorama.init(autoreset=True) 
from colorama import Fore, Back, Style

help = rf'''
{Fore.BLUE}Quack! Quack! Welcome to ......duck!
duck is a toolchain for python enthusiasts, with support for, automating scripts, tests, generating lockfiles, 
generating online documentation for your library, etc.
Find more at: http://github.com/thisismars-x/duck
'''
@click.group(help=help)
def cli():
	pass

@cli.command(help=f"{Fore.WHITE}Initialize empty project{Fore.BLUE}")
@click.option('-l', '--lib', is_flag=True, help=f'{Fore.WHITE}Initialize an empty library{Fore.BLUE}')
def init(lib):
	status = 'n'
	if os.path.exists('duck.toml'):
		status = click.prompt('TOML file already exists. Keep it? [y/n]: ', default='n')
		if status == 'y' or status == 'Y': os.remove('duck.toml')
	
	os.makedirs('tests', exist_ok=True)
	os.makedirs('debug/html', exist_ok=True)	 	
	config = {
		'meta': {
			'name': '<ProjectName>',
			'version': 0.1,
			'author': '<AuthorName>',
			'description': '<ProjectDescription>',
		},
		
		'dependencies': {
			'build' : [],
			'release': [],
		},
			
		'env': {
			'path': 'debug/ducky',
		},
	}

	config.update({
		'config' : {
			'tests': 'tests/',
		}
	})	

	if not lib: 
		config['main'] = { 'file': 'src/main.py' }
		os.makedirs('src', exist_ok=True)
		with open('src/main.py', 'w') as f: f.write("\nprint('Hello, from duck!')")
	else: os.makedirs('lib', exist_ok=True)
 
	if (not os.path.exists('duck.toml')) or (status == 'y' or status == 'Y'): 
		with open('duck.toml', 'w') as f: toml.dump(config, f)

	config = toml.load('duck.toml')
	if config['env']['path'] != 'debug/ducky':
		shutil.rmtree('debug/ducky')
		shutil.copytree(config['env']['path'], 'debug/ducky')


@cli.command(help=f"{Fore.WHITE}Generate online documentation{Fore.BLUE}")
@click.option('-c', '--close', is_flag=True, help=f"{Fore.WHITE}Use with --include to create docs for selected files only{Fore.BLUE}")
@click.option('-i', '--include', type=str, multiple=True, help=f"{Fore.WHITE}Include these files to your doc{Fore.BLUE}")
@click.option('-e', '--exclude', type=str, multiple=True, help=f"{Fore.WHITE}Exclude these files from 'src/' directory{Fore.BLUE}")
@click.option('-d', '--duck', is_flag=True, help=f"{Fore.WHITE}Open your docs in a browser. Call this only after you have called doc before.{Fore.BLUE}")
@click.option('-o', '--oopen', is_flag=True, help=f"{Fore.WHITE}Compile and open{Fore.BLUE}")
@click.option('-l', '--library', is_flag=True, help=f'{Fore.WHITE}Create online documentation for your lib/{Fore.BLUE}')
def doc(library, duck, include, close, exclude, oopen):
	
	if library: src = 'lib'
	else: src = 'src'
	if oopen: duck = False
	if not duck:
		if os.path.exists(f'/debug/html/page.html'): os.remove(f'/debug/html/page.html')
		files = [f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f))] if not close else []	
		text = ''
		
		files = list(set(files) - set(exclude))	
		
		if src == 'src':
			if 'main.py' in files:
				with open(f'src/main.py', 'r') as f:
					text += '\n'
					text += f.read()
				files.remove('main.py')
		elif src == 'lib':
			if 'lib.py' in files:	
				with open(f'lib/lib.py', 'r') as f:
					text += '\n'
					text += f.read()
				files.remove('lib.py')	


		for file in files:
			with open(f'{src}/{file}', 'r') as f:
				text += '\n'
				text += f.read()

		for file in include:
			try:
				with open(file, 'r') as f: text = text + '\n' + f.read()
			except:
				click.echo(f"Problems with including {file} in documentation. Skipping.", err=True) 

		path = os.path.expanduser('~/duck/src')
		subprocess.run([sys.executable, f'{path}/ducker.py', f'--code={text}'])

	if oopen: duck = True
	if duck:
		if not os.path.exists(f'debug/html/page.html'):
			click.echo("Could not generate docs: call duck doc (--include, --exclude, --close) to generate html first", err=True)
			return
		subprocess.run(['live-server', '--open=debug/html'])
	
@cli.command(help=f"{Fore.WHITE}Run default scripts{Fore.BLUE}")
@click.argument('argss', default='')
def run(argss):
	try: 
		cwd = os.getcwd().split('src')[0]
		file = toml.load(f'{cwd}/duck.toml')['main']['file']
		subprocess.run([sys.executable, file, argss], cwd=cwd)
	except: 
		click.echo("Problem finding file under 'main' header in duck.toml", err=True)


@cli.command(help=f"{Fore.WHITE}Run tests from tests/{Fore.BLUE}")
@click.option('-i', '--include', type=str, multiple=True, help=f"{Fore.WHITE}Run tests by including only these files from tests/{Fore.BLUE}")
def test(include):
	if not include:
		subprocess.run(['pytest', 'tests/'], cwd=os.getcwd().split('tests')[0])
	else:
		cwd = os.getcwd().split('tests')[0]
		include = [f'{cwd}/{x}' for x in include]
		subprocess.run(['pytest', include])


@cli.command(help=f"{Fore.WHITE}Inspect your dependency tree{Fore.BLUE}")
@click.option('-l', '--level', default=1, help=f'{Fore.WHITE}Get dependency tree upto 2 levels. --l2 for 2-levels.{Fore.BLUE}')
@click.option('-c', '--core', is_flag=True, help=f'{Fore.WHITE}Without duck dependencies{Fore.BLUE}')
def tree(level, core):
	core_dep = ['toml', 'click', 'colorama', 'pyfiglet', 'pytest', 'iniconfig', 'packaging', 'pluggy']
	l = level
	if l > 2: 
		click.echo(f'{Fore.RED} Can not list more than 2 levels, reverting to --l=2 instead')
		l = 2

	res_tree = dict()
	packages = subprocess.run(['pip', 'list'], stdout=subprocess.PIPE, text=True).stdout.splitlines()[2:]
	for package in packages:
		(name, version) = package.split()
		if name not in ['pip', 'pip3', 'setuptools']:
			res_tree[name] = { 'version': version }
	packages = res_tree.keys()
	for package in packages:
		sub_tree = subprocess.run(['pip', 'show', package], stdout=subprocess.PIPE, text=True).stdout.splitlines()[-2].replace('Requires: ', '').split(', ')
		res_tree[package].update({'subtree': sub_tree})
    
	res_tree_str = str()
	res_tree_dup = res_tree.copy()
	
	for keys in res_tree.keys():
		for k, v in res_tree.items():
			if k == keys: continue
			if keys in v['subtree']:
				try:
					res_tree_dup[k]['subtree'].remove(keys)
					res_tree_dup[k]['subtree'].append(f'{keys} @{res_tree[keys]["version"]}')	
					del res_tree_dup[keys]
				except: pass

	res_tree = res_tree_dup

	for (package, meta) in res_tree.items():
		if core:
			if package in core_dep: continue
		res_tree_str += f"{Fore.GREEN} |-------> {Fore.WHITE}{package} @{meta['version']}\n" if res_tree[package] else ''
		if l == 2:
			for subtrees in meta['subtree']: res_tree_str += f"{Fore.GREEN} |    |--> {Fore.BLUE}{subtrees}\n" if subtrees else ''								
			res_tree_str += f"{Fore.GREEN} |\n"
	if l==2: res_tree_str += f'\n{Fore.BLUE} Blue dependencies are required by upper white dependencies'	
	
	res_tree_str = '\n'.join(res_tree_str.splitlines())


	click.echo(res_tree_str)

@cli.command(help=f"{Fore.WHITE}Generate lockfile{Fore.BLUE}")
def lock():
	with open('freeze.txt', 'wb') as f:
		result = subprocess.run(['pip', 'freeze'], stdout=subprocess.PIPE).stdout
		f.write(result)


@cli.command(help=f"{Fore.WHITE}Upgrade packages{Fore.BLUE}")
@click.option('-p', '--pkg', type=str, default='', help=f'{Fore.WHITE}Name of package to upgrade{Fore.BLUE}')
@click.option('-v', '--version', type=str, default='', help=f'{Fore.WHITE}Version after upgrading{Fore.BLUE}')
def upgrade(pkg, version):
	if not pkg: 
		click.echo(f"{Fore.RED} Specify pkg name, see duck upgrade --help")
		return 

	if not version:
		status = click.prompt(f"{Fore.RED}It's dangerous to upgrade without specifying version.\nDo you wish to continue? [y/n]", default='n')
		if status == 'n' or status == 'N': 
			click.echo(f"{Fore.GREEN} No versions upgraded.. your lockfiles are safe")
		else: 
			try:
				subprocess.run(['pip', 'install', '--upgrade', pkg])	
				with open('freeze.txt', 'wb') as f:
					result = subprocess.run(['pip', 'freeze'], stdout=subprocess.PIPE).stdout
					f.write(result)

			except: click.echo(f"{Fore.RED} No package named {pkg}")

		return
	
	try:	
		subprocess.run(['pip', 'install', '--upgrade', f'{pkg}=={version}'])
		with open('freeze.txt', 'wb') as f:
			result = subprocess.run(['pip', 'freeze'], stdout=subprocess.PIPE).stdout
			f.write(result)

	except: click.echo(f"{Fore.RED} No package satisfies {pkg}@{version}")

@cli.command(help=f"{Fore.WHITE}Add new packages{Fore.BLUE}")
@click.option('-p', '--pkg', type=str, help=f'{Fore.WHITE}<pkg> to be installed{Fore.BLUE}')
@click.option('-r', '--release', is_flag=True, help=f'{Fore.WHITE}Bundle in release mode{Fore.BLUE}')
def add(pkg, release):
	try: 
		subprocess.run(['pip', 'install', pkg])
		config = toml.load('duck.toml')
		if not release: 
			config['dependencies']['build'].append(pkg)
			config['dependencies']['build'] = list(set(config['dependencies']['build']))
		else: 
			config['dependencies']['release'].append(pkg)
			config['dependencies']['release'] = list(set(config['dependencies']['release']))
		
		with open('duck.toml', 'w') as f: toml.dump(config, f)
	except: click.echo(f"{Fore.RED}Could not get- <{pkg}>")


@cli.command(help=f"{Fore.WHITE}Inherit dependencies from another project{Fore.BLUE}")
@click.option('-r', '--release', is_flag=True, help=f'{Fore.WHITE}Install packages for your released mode only{Fore.BLUE}')
def inherit(release):
	from_lockfile = []
	with open('freeze.txt', 'r') as f: from_lockfile = f.read().splitlines()
	if not release: 
		for pkg in from_lockfile:
			subprocess.run(['pip', 'install', pkg], stdout=open(os.devnull, 'w'))
			click.echo(f"Added <{pkg}>")
	else:
		config = toml.load('duck.toml')['dependencies']['release']
		for pkgs in from_lockfile:
			if pkgs.split('==')[0] in config: 
				subprocess.run(['pip', 'install', pkgs], stdout=open(os.devnull, 'w'))
				click.echo(f"Added <{pkgs}>")	




cli()

