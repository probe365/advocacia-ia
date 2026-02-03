import ast
import os
import re

root = r"c:\advocacia-ia-app"
file_path = os.path.join(root, "cadastro_manager.py")

with open(file_path, "r", encoding="utf-8") as f:
    tree = ast.parse(f.read(), filename=file_path)

funcs = []

class V(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        funcs.append(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        funcs.append(node.name)
        self.generic_visit(node)

V().visit(tree)

funcs = [fn for fn in funcs if not fn.startswith("__")]

all_py_files = []
for base, _, files in os.walk(root):
    for name in files:
        if name.endswith(".py"):
            path = os.path.join(base, name)
            if os.path.abspath(path) != os.path.abspath(file_path):
                all_py_files.append(path)

usage = {fn: 0 for fn in funcs}
pattern_cache = {fn: re.compile(r"\b" + re.escape(fn) + r"\b") for fn in funcs}

for path in all_py_files:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception:
        continue
    for fn, pat in pattern_cache.items():
        if pat.search(text):
            usage[fn] += 1

unused = sorted([fn for fn, count in usage.items() if count == 0])

print("UNUSED_COUNT", len(unused))
for fn in unused:
    print(fn)
