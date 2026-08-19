import os
from tree_sitter import Language, Parser
import tree_sitter_javascript

LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".swift": "swift",
    ".kt": "kotlin",
}

def get_language(filename: str) -> str:

    extension = os.path.splitext(filename)[1].lower()

    return LANGUAGE_MAP.get(extension, "unknown")


def make_js_tree(code:str):

    language = Language(tree_sitter_javascript.language())

    parser = Parser(language)
    tree = parser.parse(code.encode("utf-8"))

    return tree

def find_function_calls(node):

    calls = []

    if node.type == "call_expression":

        function_node = node.child_by_field_name("function")

        if function_node:
            calls.append(
                function_node.text.decode("utf-8")
            )

    for child in node.children:
        calls.extend(find_function_calls(child))

    return calls