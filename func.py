import re
from functools import cached_property

class Parse:
    
    def __init__(self, text):
        description = r'#\s+(?P<desc>(#.*\n)+)'
        self.func_capture = description + r'def\s+(?P<func_name>[a-zA-Z_][a-zA-Z0-9_]*)(\((?P<func_args>[^)]*)\))([ ]?->[ ]?(?P<ret_type>[a-zA-Z0-9_\.]*))?:'
        self.var_capture = description + r'(?P<var_lhs>(?!def|class)[a-zA-Z][a-zA-Z0-9_]*)\s*=(?P<var_rhs>.*)\n'
        self.text = text.read() if hasattr(text, 'read') else text

    @cached_property
    def parse_fn(self):
        res = list()
        matches = re.finditer(self.func_capture, self.text)
        if matches:
            for match in matches:
                temp = match.group('func_args').strip().split(',')
                temp = [x.strip() for x in temp]
                if '@exempt' not in match.group('desc'):
                    l1 = (match.group('desc'), match.group('func_name'), temp, match.group('ret_type'))
                    res.append(l1)
        return res
    
    @cached_property
    def parse_var(self):
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
        capture_fn = r'(?P<func_desc>(\s+#.*\n?)+)\s+def\s+(?P<func_name>[a-zA-Z_][a-zA-Z0-9_]*)(\((?P<func_args>[^)]*)\))([ ]?->[ ]?(?P<ret_type>[a-zA-Z0-9_]*))?:'
        capture_var = r'(?P<var_desc>(\s+#.*\n?)+)\s+(?P<var_lhs>(?!def|class)[a-zA-Z][a-zA-Z0-9_]*)\s*=(?P<var_rhs>.*)\n'
        res = dict()
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
    text = str(str(str(text[1:].strip()).replace('\n', '<br>')).replace('\t', '    '))
    hrefs = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    text = re.sub(hrefs, r'<a href="\2">\1</a>', text)
    codeblocks = r'''
    <div class="codeblock">
        <p class="block-header">CODE</p>
        <code class="block-main">\1 </code>
    </div>
    '''
    code = r'`code(.*)`'
    text = re.sub(code, codeblocks, text)
    exampleblocks = r'''
    <div class="exampleblock">
        <p class="block-header">EXAMPLE</p>
        <code class="block-main">\1 </code>
    </div>
    '''
    example = r'`example(.*)`'
    text = re.sub(example, exampleblocks, text)
    errorblocks = r'''
    <div class="errorblock">
        <p class="block-header">ERROR</p>
        <code class="block-main">\1 </code>
    </div>
    '''
    error = r'`error(.*)`'
    text = re.sub(error, errorblocks, text)
    bold = r'\*\*([^<br>]*)\*\*'
    text = re.sub(bold, r'<b>\1</b>', text)
    return ''.join(list(map(lambda x: x.strip(), text.split('#'))))

def func_header(func_headers):
    desc, name, arg, ret = func_headers
    arg = ', '.join(arg)
    desc = get_desc(desc)
    if ret:
        return rf'''
        <div class="func-block" id="{name}">
            <h3> {name}: [{arg}] -> {ret} </h3>
            <p class="desc"> {desc} </p>
        </div>
        '''
    else:
        return rf'''
        <div class="func-block" id="{name}">
            <h3> {name}: [{arg}] </h3>
            <p class="desc"> {desc} </p>
        </div>
        '''

def var_header(var_headers):
    desc, lhs, rhs = var_headers
    desc = get_desc(desc)
    return rf'''
    <div class="var-block" id="{lhs}">
        <h3> {lhs} = {rhs} </h3>
        <p class="desc"> {desc} </p>
    </div>
    '''

def cls_header(cls_name, cls_headers):
    cls_desc, cls_func, cls_var = get_desc(cls_headers["class-desc"]), cls_headers["class-fn"], cls_headers["class-var"]
    res = rf'''
    <div class="class-block" id="{cls_name}">
        <h3> {cls_name} </h3>
        <p class="desc"> {cls_desc} </p>
    '''
    n_func = len(cls_func)
    if n_func > 0:
        res += rf'''
        <h4> Class Functions </h4>'''
        for func in cls_func:
            desc, name, arg, ret = func
            arg = ', '.join(arg)
            desc = get_desc(desc)
            if ret:
                res += rf'''
                <div class="class-func">
                    <p><strong>{name}: [{arg}] -> {ret}</strong></p>
                    <p class="desc">{desc}</p>
                </div>
                '''
            else:
                res += rf'''
                <div class="class-func">
                    <p><strong>{name}: [{arg}]</strong></p>
                    <p class="desc">{desc}</p>
                </div>
                '''
    n_var = len(cls_var)
    if n_var > 0:
        res += rf'''
        <h4> Class Variables </h4>'''
        for var in cls_var:
            desc, lhs, rhs = var
            desc = get_desc(desc)
            res += rf'''
            <div class="class-var">
                <p><strong>{lhs} = {rhs}</strong></p>
                <p class="desc">{desc}</p>
            </div>
            '''
    res += rf'''
    </div>'''
    return res

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
    <h2> Functions </h2>
    '''
    for functions in parsed["functions"]:
        fn_html += func_header(functions)
        overview_fn += rf'''<li><a href="#{functions[1]}"> {functions[1]} </a></li>'''

if len(parsed["variables"]):
    var_html += r'''
    <h2> Variables </h2>
    '''
    for variables in parsed["variables"]:
        var_html += var_header(variables)
        overview_var += rf'''<li><a href="#{variables[1]}"> {variables[1]} </a></li>'''

if len(parsed["class-names"]):
    class_html += r'''
    <h2> Classes </h2>
    '''
    for class_names in parsed["class-names"]:
        class_html += cls_header(class_names, parsed["classes"][class_names])
        overview_cls += rf'''<li><a href="#{class_names}"> {class_names} </a></li>'''

headers = rf'''
<h2> Overview </h2>
[TOP SUMMARY]
<div class="summary">
    <div class="functions">
        <h3> Functions </h3>
        <ol>
        [FUNCTIONS]
        </ol>
    </div>
    <div class="variables">
        <h3> Variables </h3>
        <ol>
        [VARIABLES]
        </ol>
    </div>
    <div class="class">
        <h3> Classes </h3>
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
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700&family=Roboto&display=swap" rel="stylesheet">
</head>
<body>
    <div class="head">
        <img src="duck.jpg" class="logo" alt="duck duck" title="duck duck"></img>
        <h1>duck: A Python Professional's Toolchain</h1>
    </div>
    <p id="head-end">Documentation generated by duck</p>
    <hr>
    <div class="container">
        [HEADERS]
        [FUNCTIONS]
        [VARS]
        [CLASSES]
    </div>
</body>

<style>
    @font-face {
      font-family: "Iosevka";
      src: url("fonts/Iosevka1.ttf") format("truetype");
      font-weight: normal;
      font-style: normal;
    }
    :root {
        --primary-color: #2C3E50;
        --secondary-color: #ECF0F1;
        --accent-color: #3498DB;
        --error-color: #E74C3C;
        --success-color: #27AE60;
        --background-color: #FFFFFF;
        --text-color: #333333;
    }
    html {
        font-family: 'Roboto', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Montserrat', sans-serif;
    }
    code, .codeblock, .errorblock, .exampleblock {
        font-family: 'Iosevka', monospace;
    }
    body {
        background-color: var(--background-color);
        color: var(--text-color);
        line-height: 1.6;
        margin: 0;
        padding: 0;
    }
    .head {
        background-color: var(--primary-color);
        color: #FFFFFF;
        padding: 20px;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
    }
    .head h1 {
        margin: 0;
        font-size: 24px;
    }
    .logo {
        border-radius: 50%;
        width: 50px;
        height: 50px;
        margin-right: 20px;
    }
    #head-end {
        text-align: right;
        font-size: 12px;
        color: #777;
        margin: 10px 0;
    }
    .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    .summary {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-bottom: 40px;
    }
    .summary ol {
        list-style: none;
        padding: 0;
    }
    .summary li {
        margin-bottom: 10px;
    }
    .summary a {
        display: block;
        padding: 5px;
        border-radius: 3px;
        transition: background-color 0.3s;
    }
    .summary a:hover {
        background-color: rgba(0,0,0,0.05);
    }
    .func-block, .var-block, .class-block {
        background-color: var(--secondary-color);
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .func-block h3, .var-block h3, .class-block h3 {
        color: var(--primary-color);
    }
    .codeblock, .errorblock, .exampleblock {
        background-color: #272822;
        color: #F8F8F2;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        overflow-x: auto;
    }
    .block-header {
        font-weight: bold;
        padding: 5px;
        border-radius: 3px;
        margin: 0;
    }
    .codeblock .block-header {
        background-color: var(--accent-color);
    }
    .errorblock .block-header {
        background-color: var(--error-color);
    }
    .exampleblock .block-header {
        background-color: var(--success-color);
    }
    .block-main {
        display: block;
        margin-top: 10px;
        font-size: 14px;
        white-space: pre-wrap;
    }
    a {
        color: var(--accent-color);
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    .top-summary {
        background-color: var(--secondary-color);
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 30px;
    }
    #top-summary-desc {
        font-weight: bold;
        color: var(--primary-color);
    }
    .class-func, .class-var {
        margin-left: 20px;
    }
    @media (max-width: 768px) {
        .head {
            flex-direction: column;
            text-align: center;
        }
        .logo {
            margin-bottom: 10px;
        }
        #head-end {
            text-align: center;
            margin: 10px 0;
        }
        .summary {
            grid-template-columns: 1fr;
        }
        .codeblock, .errorblock, .exampleblock {
            width: 100%;
        }
        .container {
            padding: 10px;
        }
    }
</style>
</html>
'''

final = base_html.replace('[HEADERS]', headers).replace('[FUNCTIONS]', fn_html).replace('[VARS]', var_html).replace('[CLASSES]', class_html)

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