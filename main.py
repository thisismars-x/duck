import ast, re

def parse_function_args(args):
    parsed_args = []
    for arg in args.args:
        arg_name = arg.arg
        arg_annotation = ast.unparse(arg.annotation) if arg.annotation else None
        parsed_args.append((arg_name, arg_annotation))

    return parsed_args

def parse_fn(func_node):
    func_name = func_node.name
    params = parse_function_args(func_node.args)
    return_type = ast.unparse(func_node.returns) if func_node.returns else None
    
    docstring = ast.get_docstring(func_node)
    
    return {
        'name': func_name,
        'params': params,
        'return_type': return_type,
        'docstring': docstring
    }

def parse_cls(class_node):
    class_docstring = ast.get_docstring(class_node)
    
    if not class_docstring:
        return None

    class_details = {
        'class_name': class_node.name,
        'docstring': class_docstring,
        'methods': []
    }

    for item in class_node.body:
        if isinstance(item, ast.FunctionDef):
            method_details = parse_fn(item)
            if method_details['docstring']:
                class_details['methods'].append(method_details)

    return class_details

def parse_module(path):
    with open(path, 'r') as file:
        file_content = file.read()
    
    tree = ast.parse(file_content)
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Str):
        toplevel = tree.body[0].value.s
    else: toplevel = ''
    classes = {}
    functions = {}

    class_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    for class_node in class_nodes:
        class_details = parse_cls(class_node)
        if class_details:  # Only add class if it has a docstring
            classes[class_details['class_name']] = {
                'docstring': class_details['docstring'],
                'methods': {}
            }
            for method in class_details['methods']:
                classes[class_details['class_name']]['methods'][method['name']] = {
                    'params': method['params'],
                    'return_type': method['return_type'],
                    'docstring': method['docstring']
                }
    
    remaining_nodes = [node for node in tree.body if not isinstance(node, ast.ClassDef)]
    for node in remaining_nodes:
        if isinstance(node, ast.FunctionDef):
            function_details = parse_fn(node)
            if function_details['docstring']:
                functions[function_details['name']] = {
                    'params': function_details['params'],
                    'return_type': function_details['return_type'],
                    'docstring': function_details['docstring']
                }
    
    return {
	'toplvl' : toplevel,
        'classes': classes,
        'functions': functions,
    }

# ----------------------------------------------------
# All parsing is done. Now generating html.

def dilute_desc(doc):
	''' Handle code, error, example- blocks, hyperlinks, bold-text 
	Every text is rendered here first.'''

	doc = doc.replace('\n', '<br>').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;').replace(' ', '&nbsp;')
	doc = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2"> \1 </a>', doc)

	blocks = r'''
		<div class="[X]block">
			<p id="[X]block-h"> [X] </p>
			<code id="[X]block-main" style="font-size: 14px;"> \1 </code>
		</div>
	'''

	doc = re.sub(r'`code(.*)`', str(blocks.replace('[X]', 'code')), doc)
	doc = re.sub(r'`error(.*)`', str(blocks.replace('[X]', 'error')), doc)
	doc = re.sub(r'`example(.*)`', str(blocks.replace('[X]', 'example')), doc)
	doc = re.sub(r'\*\*(.*)\*\*', r'<b> \1 </b>', doc)
	return doc

def dilute_fn(functions):
	''' Handles all functions at once '''
	func_html = '<h1> Functions </h1>'
	overview_fn = ''

	for name, others in functions.items():
		args = ''
		for x in others['params']:
			if not x[1]: args += f'{x[0]}, '
			else: args += f'{x[0]}: {x[1]}, '
		args = args[:-2]
		
		overview_fn += rf'<li><a href="#{name}"> {name} </a></li>' 
		if others['return_type']:
			func_html += rf'''
				<div class="func-block" id="{name}">
				    <h2 font-weight="bolder"> {name}: [{args}] -> {others['return_type']} </h2>
				    <p id="func-desc"> {dilute_desc(others['docstring'])} </p>
				</div>
			'''
		else:
			func_html +=  rf'''
				<div class="func-block" id="{name}">
				    <h2 font-weight="bolder"> {name}: [{args}] </h2>
				    <p> {dilute_desc(others['docstring'])} </p>
				</div>
			'''
	return func_html, overview_fn


def dilute_cls(classes):
	''' Handles all classes at once '''
	cls_html = '<h1> Classes </h1>'
	overview_cls = ''
		
	for name, others in classes.items():
		overview_cls += rf'<li><a href="#{name}"> {name} </a></li>'
		cls_html += rf'''
			<div class="class-block" id="{name}">
				<h1> {name} </h1>
				<p> {dilute_desc(others['docstring'])} </p>
			</div>
		'''
		
		cls_html += f'<h2 class="cls-func-block"> Functions - {name} </h2>'
		for fname, other in others['methods'].items():
			args = ''
			for x in other['params']:
				if not x[1]: args += f'{x[0]}, '
				else: args += f'{x[0]}:  {x[1]}, '
			args = args[:-2]
			
			if not other['return_type']:
				cls_html +=  rf'''
					<div class="cls-func-block" id="{fname}">
						<div id="cls-func-block-h">
						<h2 font-weight="bolder"> {fname}: [{args}] </h2>
						<p> {dilute_desc(other['docstring'])} </p>
						</div>
					</div>
				'''
			else:
				cls_html +=  rf'''
					<div class="cls-func-block" id="{fname}">
						<div id="cls-func-block-h">
						<h2 font-weight="bolder"> {fname}: [{args}] -> {other['return_type']}  </h2>
						<p> {dilute_desc(other['docstring'])} </p>
						</div>
					</div>
				'''
	return cls_html, overview_cls

def dilute_header(toplevel):
	return rf'''
		<div class="toplevel"> 
			<h1> Description </h1>
			<p> {dilute_desc(toplevel)} </p>
		</div>
	'''


base_html = r'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>duck</title>
    <link rel="icon" href="logo.svg" type="image/x-icon">

</head>
<body>
    <div class="head">
        <img src="duck.jpg" class="logo" alt="duck duck" title="duck duck"></img>
        <h1>duck: A Python Professional's Toolchain</h1>
    </div>
    <p id="head-end">Documentation generated by duck</p>
    <hr>
    
    [HEADER]
    [FUNCTION]
    [CLASS]
    
</body>

<style>
    @font-face {
      font-family: "Iosevka";
      src: url("fonts/Iosevka1.ttf") format("truetype");
      font-weight: normal;
      font-style: normal;
    }
    html {
        font-family: 'Iosevka'; 
    }
    
    .head {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
    }

    #head-end {
        margin-left: 80%;
        margin-top: -3%;
    }

    .logo {
        border-radius: 50%;
        width: 75px;
        height: 75px;
        margin: 10px;
    }

    .func-block{
        padding-left: 10%;
    }
    
    .cls-func-block {
		padding-left: 10%;
        #cls-func-block-h {
			padding-left: 12%;
        }
    }

    body {
        word-wrap: break-word;
        word-break: keep-all;
    }

    .var-block {
        padding-left: 10%;
    }

    .class-block {
        padding-left: 10%;
    }

    .codeblock {
        background-color: black;
        color:white;
        width: 35%;
        
        #codeblock-h {
            font-weight: bolder;
            background-color: blue;
            text-align: center;
        }
    }
    
    .errorblock {
        background-color: black;
        color:white;
        width: 35%;
        
        #errorblock-h {
            font-weight: bolder;
            background-color: red;
            text-align: center;
        }
    }

    .exampleblock {
        background-color: black;
        color:white;
        width: 35%;
        
        #exampleblock-h {
            font-weight: bolder;
            background-color: green;
            text-align: center;
        }
    }

    a {
        text-decoration: none;
    }

    .toplevel, .summary-wrapper {
        background-color: #EEDCDC;
        width: 90%;
        padding: 10px;
        margin-left: 4%;
    }
    
    .summary {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        width: 50%;
    }
</style>
</html>
'''




# ------------------------------
# now take in file and spit html back at ya'
import argparse
parser = argparse.ArgumentParser(description="What file do you want doc for?")
parser.add_argument("--filename", help="filename?", default="file.py")
parser.add_argument("--output", help="output filename?", default="index.html")
args = parser.parse_args()



with open(args.output, 'w') as f:
  res = parse_module(args.filename)
  header, cls_html, fn_html, summary_cls, summary_fn = '', '', '', '', ''
  if res['toplvl']: header = dilute_header(res['toplvl'])
  if res['classes']: cls_html, summary_cls = dilute_cls(res['classes'])
  if res['functions']: fn_html, summary_fn = dilute_fn(res['functions'])

  header = rf'''
	{header}
		<div class="summary-wrapper">
		<div class="summary">
		    <div class="functions">
		        <h2> Functions </h2>
		        <ol>
		        [FUNCTION]
		        </ol>
		    </div>
		    <div class="class">
		        <h2> Classes </h2>
		        <ol>
		        [CLASS]
		        </ol>
		    </div>
		</div>
	</div>
	'''.replace('[FUNCTION]', summary_fn).replace('[CLASS]', summary_cls)

  html = base_html.replace('[HEADER]', header).replace('[FUNCTION]', fn_html).replace('[CLASS]', cls_html)
  f.write(html)
