"""Check the Dagster code in a ticket body against the installed Dagster, so a wrong suggestion is refused."""

import ast
import contextlib
import importlib
import inspect
import re

FENCE = re.compile(r"```([a-zA-Z]*)\n(.*?)```", re.DOTALL)
IMPORT_LINE = re.compile(r"^\s*(from\s+dagster[\w.]*\s+import\s+.+|import\s+dagster[\w.]*(\s+as\s+\w+)?)\s*$")


def _new_code(block: str) -> str:
    lines = block.splitlines()
    if not any(line.startswith(("+", "-")) for line in lines):
        return block
    return "\n".join(line[1:] for line in lines if line.startswith(("+", " ")) and not line.startswith("+++"))


def _resolve(root: str, chain: list[str]):
    obj = importlib.import_module(root.split(".")[0])
    for part in [*root.split(".")[1:], *chain]:
        if hasattr(obj, part):
            obj = getattr(obj, part)
        else:
            try:
                obj = importlib.import_module(f"{obj.__name__}.{part}")
            except (ImportError, AttributeError):
                return None
    return obj


def _chain(node) -> list[str] | None:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    return [node.id, *reversed(parts)] if isinstance(node, ast.Name) else None


def _check_tree(tree: ast.AST, problems: list[str], aliases: dict[str, str] | None = None) -> None:
    aliases = {} if aliases is None else aliases
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] == "dagster":
                    aliases[a.asname or a.name.split(".")[0]] = a.name
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "dagster":
            try:
                module = importlib.import_module(node.module)
            except ImportError:
                problems.append(f"line {node.lineno}: module {node.module} does not exist")
                continue
            for a in node.names:
                if a.name != "*" and not hasattr(module, a.name):
                    problems.append(f"line {node.lineno}: {node.module} has no {a.name}")
                aliases[a.asname or a.name] = f"{node.module}.{a.name}"
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            chain = _chain(node)
            if chain and chain[0] in aliases and aliases[chain[0]] == "dagster" and len(chain) == 2:
                if _resolve("dagster", chain[1:]) is None:
                    problems.append(f"line {node.lineno}: dagster has no {chain[1]}")
        if not isinstance(node, ast.Call):
            continue
        chain = _chain(node.func)
        if not chain or chain[0] not in aliases:
            continue
        obj = _resolve(aliases[chain[0]], chain[1:])
        if obj is None or any(isinstance(a, ast.Starred) for a in node.args) or any(k.arg is None for k in node.keywords):
            continue
        try:
            signature = inspect.signature(obj)
        except (TypeError, ValueError):
            continue
        try:
            signature.bind(*[object()] * len(node.args), **{k.arg: object() for k in node.keywords})
        except TypeError as e:
            problems.append(f"line {node.lineno}: {'.'.join(chain)}{signature} does not accept this call ({e})")


def problems_in(body: str) -> list[str]:
    """Problems found in the Python and diff code blocks of a ticket body; empty when it is sound."""
    problems: list[str] = []
    for lang, block in FENCE.findall(body):
        if lang.lower() not in ("", "python", "py", "diff"):
            continue
        code = _new_code(block)
        try:
            _check_tree(ast.parse(code), problems)
        except SyntaxError:
            _check_by_line(code, problems)
    return problems


def _check_by_line(code: str, problems: list[str]) -> None:
    """For a fragment that does not parse as a whole: check its imports, then each line on its own."""
    aliases: dict[str, str] = {}
    lines = [line.strip() for line in code.splitlines() if line.strip()]
    for line in lines:
        if IMPORT_LINE.match(line):
            with contextlib.suppress(SyntaxError):
                _check_tree(ast.parse(line), problems, aliases)
    for line in lines:
        if not IMPORT_LINE.match(line):
            with contextlib.suppress(SyntaxError):
                _check_tree(ast.parse(line), problems, aliases)
