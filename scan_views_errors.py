import ast
import re
from collections import defaultdict

def scan_python_file(filepath):
    print(f"\n Scanning file: {filepath}")
    issues = []

    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            code = file.read()
    except Exception as e:
        print(f" Error reading file: {e}")
        return

    triple_quote_matches = re.findall(r'("""|\'\'\')', code)
    if len(triple_quote_matches) % 2 != 0:
        issues.append(" Unterminated triple-quoted string detected.")

    try:
        tree = ast.parse(code)
        func_counts = defaultdict(int)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_counts[node.name] += 1
        for name, count in func_counts.items():
            if count > 1:
                issues.append(f" Duplicate function definition: {name} appears {count} times")
    except SyntaxError as e:
        issues.append(f" SyntaxError: {e.msg} at line {e.lineno}")
        return report_issues(issues)

    required_imports = [
        'from django.shortcuts import render', 'from django.contrib import messages',
        'from django.utils import timezone', 'from datetime import timedelta'
    ]
    for imp in required_imports:
        if imp not in code:
            issues.append(f" Missing import: {imp}")

    lines = code.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith('elif') and (i == 0 or not lines[i-1].strip().startswith(('if', 'elif', 'else'))):
            issues.append(f" Line {i+1}: 'elif' used without a proper preceding 'if'")
        if line.strip().startswith('if') and not lines[i+1].startswith((' ', '\t')):
            issues.append(f" Line {i+2}: IndentationError  expected an indented block after 'if'")

    return report_issues(issues)

def report_issues(issues):
    if not issues:
        print(" No major issues found.")
    else:
        for issue in issues:
            print(issue)

# === Run this on your views.py ===
if __name__ == "__main__":
    scan_python_file("views.py")
