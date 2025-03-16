import re
from functools import cached_property

class Parse:
    
    def __init__(self, text):
        description =r'#\s+(?P<desc>(#.*\n)+)'

        self.func_capture = description + r'def\s+(?P<func_name>[a-zA-Z_][a-zA-Z0-9_]*)(\((?P<func_args>[^)]*)\))([ ]?->[ ]?(?P<ret_type>[a-zA-Z0-9_\.]*))?:'
 
        self.var_capture = description + r'(?P<var_lhs>(?!def|class)[a-zA-Z][a-zA-Z0-9_]*)\s*=(?P<var_rhs>.*)\n'

        self.text = text.read() if hasattr(text, 'read') else text

    @cached_property
    def parse_fn(self):
        # ['desc', 'func_name', 'func_args', 'ret_type']
        res = list() 
        matches = re.finditer(self.func_capture, self.text)

        if matches:
            for match in matches:
                temp = match.group('func_args').strip().split(',')
                temp = [x.strip() for x in temp]
                
                if '@exempt' not in match.group('desc'):
                    l1 = (match.group('desc'), match.group('func_name'),temp, match.group('ret_type'))
                    res.append(l1)

        return res
    
    @cached_property
    def parse_var(self):
        # ['desc', 'var_lhs', 'var_rhs']
        res = list()
        matches = re.finditer(self.var_capture, self.text)

        if matches:
            for match in matches:

                if '@exempt' not in match.group('desc'):
                    l2 = (match.group('desc'), match.group('var_lhs').strip(), match.group('var_rhs').strip())
                    res.append(l2)

        return res
    
    @cached_property
    def parse_class(self):
        class_c = r'#\s+(?P<class_desc>(#.*\n?)+)class\s(?P<class_name>.*):'
        string = self.text
        x = re.finditer(class_c, string)
        class_names = list()
        class_desc = list()

        if x:
            for match in x:
                class_names.append(match.group('class_name'))
                class_desc.append(match.group('class_desc'))

        class_body = list()

        class_breaker = str()
        for class_name in class_names:
            class_breaker += rf'#\s+(#.*\n?)+(?P<{class_name}>class {class_name}:.*)'

        classes = re.search(class_breaker, string, re.DOTALL)
        for class_name in class_names:
            body = classes.group(class_name)
            class_body.append(body)

        # parse function within classes 
        capture_fn = r'(?P<func_desc>(\s+#.*\n?)+)\s+def\s+(?P<func_name>[a-zA-Z_][a-zA-Z0-9_]*)(\((?P<func_args>[^)]*)\))([ ]?->[ ]?(?P<ret_type>[a-zA-Z0-9_]*))?:'

        # parse variable within classes
        capture_var = r'(?P<var_desc>(\s+#.*\n?)+)\s+(?P<var_lhs>(?!def|class)[a-zA-Z_][a-zA-Z0-9_]*)\s*=(?P<var_rhs>.*)\n'

        # some_fns = re.finditer(capture_fn, class_body[0])

        res = dict() 
        # { class-name: { class-desc, fn, var}}

        for (i, name) in enumerate(class_names):
            temp = dict()
            temp['class-desc'] = class_desc[i]
            temp['class-fn'], temp['class-var'] = list(), list()
            
            all_fns = re.finditer(capture_fn, class_body[i])
            for fn in all_fns:
                args = fn.group('func_args').strip().split(',')
                args = [x.strip() for x in args]
                fn_desc = fn.group('func_desc')
                fn_name = fn.group('func_name')
                ret_type = fn.group('ret_type')
                
                try:
                    if '@exempt' in fn_desc: break 
                except: pass
                if '##' not in re.sub('\s', '', fn_desc):
                    temp['class-fn'].append((fn_desc, fn_name, args, ret_type))
            all_vars = re.finditer(capture_var, class_body[i])
            for var in all_vars:
                if '##' not in re.sub('\s', '', var.group('var_desc')):
                    temp['class-var'].append([var.group('var_desc'), var.group('var_lhs').strip(), var.group('var_rhs').strip()])

            res[name] = temp
        return res, class_names

    @cached_property
    def parse_head(self):
        module = r'#\s*\-[\-.]*\n(?P<module_summary>(#[^\n]*\n)*)'
        match = re.search(module, self.text, re.DOTALL)
        
        return match.group('module_summary') if match else ''


    def begin_parse(self, fmt='dict', f='abc.json'):
        # Return { functions: [ [] ], variables: [ [] ], classes: { {} }}
        final = {
            'functions': self.parse_fn,
            'variables': self.parse_var,
            'classes': self.parse_class[0],
            'class-names': self.parse_class[1],
            'head': self.parse_head,
        }

        if fmt != 'json': return final 
        else:
            import json 
            final = json.dumps(final, indent=4)
            with open(f, 'w') as f:
                f.write(final)

def get_desc(text):
    # escapes \n and \t. What else?
    text = str(str(str(text[1:].strip()).replace('\n', '<br>')).replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;'))
    # first, handling links 
    # [text](link) typical markdown style
    hrefs = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    text = re.sub(hrefs, r'<a href="\2">\1</a>', text)

    # handling `code` blocks
    # code blocks start with `code and end with a single line with # `
    codeblocks = r'''
    <div class="codeblock">
    	<p id="codeblock-h">CODE</p>
        <code id="codeblock-main" style="font-size: 14px;">\1 </code>
    </div>
    '''
    code = r'`code(.*)`'
    text = re.sub(code, codeblocks, text)

	# handling `example` blocks
    # code blocks start with `example and end with a single line with # `
    exampleblocks = r'''
    <div class="exampleblock">
    	<p id="exampleblock-h">EXAMPLE</p>
        <code id="exampleblock-main" style="font-size: 14px;">\1 </code>
    </div>
    '''
    example = r'`example(.*)`'
    text = re.sub(example, exampleblocks, text)
    
	# handling `error` blocks
    # code blocks start with `error and end with a single line with # `
    errorblocks = r'''
    <div class="errorblock">
    	<p id="errorblock-h">ERROR</p>
        <code id="errorblock-main" style="font-size: 14px;">\1 </code>
    </div>
    '''
    error = r'`error(.*)`'
    text = re.sub(error, errorblocks, text)


    # handling bold text 
    # **text** typical markdown style 
    bold = r'\*\*([^<br>]*)\*\*'
    text = re.sub(bold, r'<b>\1</b>', text)

    return ''.join(list(map(lambda x: x.strip(), text.split('#'))))

def func_header(func_headers):
    desc, name, arg, ret = func_headers

    # arg printed as {} gives weird list with trailing ,
    arg = ', '.join(arg)
    desc = get_desc(desc)
    if ret:
        return rf'''
        <div class="func-block" id="{name}">
            <h2 font-weight="bolder"> {name}: [{arg}] -> {ret} </h2>
            <p id="func-desc"> {desc} </p>
        </div>
        '''
    else:
        return rf'''
        <div class="func-block" id="{name}">
            <h2 font-weight="bolder"> {name}: [{arg}] </h2>
            <p> {desc} </p>
        </div>
        '''

def var_header(var_headers):
    desc, lhs, rhs = var_headers
    desc = get_desc(desc)
    return rf'''
    <div class="var-block" id="{lhs}">
        <h2 font-weight="bolder"> {lhs} = {rhs} </h2>
        <p> {desc} </p>
    </div>
    '''

def cls_header(cls_name, cls_headers):
    # cls_fun and cls_var are iterables of func/vars not single items
    cls_desc, cls_func, cls_var = get_desc(cls_headers["class-desc"]), cls_headers["class-fn"], cls_headers["class-var"]
    res = rf'''
    <div class="class-block" id="{cls_name}">
        <h1> {cls_name} </h1>
        <p> {cls_desc} </p>
    '''
    
    n_func = len(cls_func)
    if n_func > 0:
        res += rf'''
        <h1> Class Functions: </h1>'''
        for i in range(n_func):
            res += func_header(cls_func[i])

    n_var = len(cls_var)
    if n_var > 0:
        res += rf'''
        <h1> Class Variables: </h1>'''
        for i in range(n_var):
            res += var_header(cls_var[i])

    res += rf'''
    </div>'''
    return res


# ------------------------------------------------------
# provide file-path as command line argument

import argparse
parser = argparse.ArgumentParser(description="What file do you want doc for?")
parser.add_argument("--filename", help="filename?")
parser.add_argument("--output", help="output filename?", default="page.html")
args = parser.parse_args()


parsed = Parse(open(args.filename)).begin_parse()

fn_html, var_html, class_html = rf'''''', rf'''''', rf''''''
overview_fn, overview_var, overview_cls = rf'''''', rf'''''', rf''''''

if len(parsed["functions"]):
    fn_html += r'''
    <h1 font-weight="bolder"> Functions: </h1>
    '''
    for functions in parsed["functions"]:
        fn_html += func_header(functions)
        overview_fn += rf'''<li><a href="#{functions[1]}"> {functions[1]} </a></li>'''

if len(parsed["variables"]):
    var_html += r'''
    <h1 font-weight="bolder"> Variables: </h1>
    '''
    for variables in parsed["variables"]:
        var_html += var_header(variables)
        overview_var += rf'''<li><a href="#{variables[1]}"> {variables[1]} </a></li>'''

if len(parsed["class-names"]):
    class_html += r'''
    <h1 font-weight="bolder"> Classes: </h1>
    '''
    for class_names in parsed["class-names"]:
        class_html += cls_header(class_names, parsed["classes"][class_names])
        overview_cls += rf'''<li><a href="#{class_names}"> {class_names} </a></li>'''


headers = rf'''
<h1> Overview </h1> 
[TOP SUMMARY]
<div class="summary">
    <div class="functions">
        <h2> Functions </h2>
        <ol>
        [FUNCTIONS]
        </ol>
    </div>
    <div class="variables">
        <h2> Variables </h2>
        <ol>
        [VARIABLES]
        </ol>
    </div>
    <div class="class">
        <h2> Classes </h2>
        <ol>
        [CLASSES]
        </ol>
    </div>
</div>
'''

headers = headers.replace('[FUNCTIONS]', overview_fn).replace('[VARIABLES]', overview_var).replace('[CLASSES]', overview_cls)


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
    
    [HEADERS]

    [FUNCTIONS]
    [VARS] 
    [CLASSES]
    
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

    .summary {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        width: 80%;
        padding-left: 4%;
    }

    a {
        text-decoration: none;
    }

    .top-summary {
        background-color: #EEDCDC;
        width: 90%;
        padding: 10px;
        margin-left: 4%;

        #top-summary-desc {
            font-weight: bolder;
        }
    }
</style>
</html>
'''

# this is the final html file 
final = base_html.replace('[HEADERS]', headers).replace('[FUNCTIONS]', fn_html).replace('[VARS]', var_html).replace('[CLASSES]', class_html)

# ----------------------------------------------------
# Module level description
summary = get_desc(parsed["head"])
summary = rf'''
    <div class="top-summary">
        <p id="top-summary-desc"> {summary} </p>
    </div>
''' if summary else ''

final = final.replace('[TOP SUMMARY]', summary)

    
with open(args.output, 'w') as f:
    f.write(final)
    print(f"done writing {args.output}")

