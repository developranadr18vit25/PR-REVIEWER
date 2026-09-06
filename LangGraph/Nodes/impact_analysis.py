import os
import ast
from collections import defaultdict, deque
from unidiff import PatchSet

from workFlow import PR_State


def get_changed_lines(patch):  # THIS PROVIDES THE LINES WHERE CHANGED HAVE BEEN OCCURRED INSIDE THE PATCH

    changed_lines = []

    if not patch:
        return changed_lines

    patch_set = PatchSet(patch)

    for file in patch_set:

        for hunk in file:

            for line in hunk:

                if line.is_added:
                    changed_lines.append(
                        line.target_line_no
                    )

    return changed_lines


def get_functions(code):   # THIS PROVIDES ALL FUNCTION 

    functions = []

    try:
        tree = ast.parse(code)

    except SyntaxError:
        return functions

    for node in ast.walk(tree):

        if isinstance(node, ast.FunctionDef):

            functions.append({
                "name": node.name,
                "start": node.lineno,
                "end": node.end_lineno
            })

    return functions

def find_changed_functions(code, changed_lines):  # THIS GIVES ALL THE FUNCTIONS WHICH LIE WITHIN THE RANGE OF THE CHANGED LINES 

    functions = get_functions(code)

    changed_functions = []

    for function in functions:

        for line in changed_lines:

            if (
                function["start"]
                <= line
                <= function["end"]
            ):

                changed_functions.append(
                    function
                )

                break

    return changed_functions

def get_called_functions(function_node): # THIS FINDS THE FUNCTIONS CALLED INSIDE A FUNCTION

    called_functions = []

    for node in ast.walk(function_node):

        if not isinstance(node, ast.Call):
            continue

        if isinstance(node.func, ast.Name):

            called_functions.append(
                node.func.id
            )

        elif isinstance(node.func, ast.Attribute):

            called_functions.append(
                node.func.attr
            )

    return called_functions
    

def build_call_graph(worktree):   # THIS FUNCTION CREATES A GRAPH WHERE FOR EACH FUNCTIONS , WE HAVE TO STORED FUNCTIONS WHICH ARE RELATED TO IT OR CALLED INSIDE IT
# WE ALSO CREAT A FUNCTIONS DICTONARY WHICH STORES INFO ABOUT A FUNCTION LIKE WHICH FILE IS IT PRESENT AND ALL 

    graph = defaultdict(list)

    functions = {}

    for root, dirs, files in os.walk(worktree):

        dirs[:] = [
            d for d in dirs
            if d not in [
                ".git",
                "__pycache__",
                ".venv",
                "venv"
            ]
        ]

        for filename in files:

            if not filename.endswith(".py"):
                continue

            path = os.path.join(
                root,
                filename
            )

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as file:

                    code = file.read()

                tree = ast.parse(code)

            except Exception:
                continue

            relative_path = os.path.relpath(
                path,
                worktree
            )

            for node in ast.walk(tree):

                if not isinstance(
                    node,
                    ast.FunctionDef
                ):
                    continue

                function_name = node.name

                function_id = (
                    relative_path,
                    function_name
                )

                functions[function_id] = {
                    "filename": relative_path,
                    "function": function_name,
                    "start": node.lineno,
                    "end": node.end_lineno
                }

                called_functions = (
                    get_called_functions(node)
                )

                for called in called_functions:

                    graph[function_id].append(
                        called
                    )

    return graph, functions


def resolve_graph(graph, functions):
    
    # WE MODIFY THE GRAPH AS PREVIOUSLY WE HAVE FUNCTION NAME,ID -> FUNCTION AND NOW WE MAKE IT FUNCTION NAME , ID -> FUNCTION NAME, ID
    #THIS HELPS TO KNOW THAT WHICH FILE THE FUNCTIONS BELONG TO 

    name_to_functions = defaultdict(list)

    for function_id in functions:

        name = function_id[1]

        name_to_functions[name].append(
            function_id
        )

    new_graph = defaultdict(list)

    for caller in graph:

        for called_name in graph[caller]:

            possible_functions = (
                name_to_functions[called_name]
            )

            for function in possible_functions:

                new_graph[caller].append(
                    function
                )

    return new_graph

# 7. REVERSE THE GRAPH

def reverse_graph(graph):

    reverse = defaultdict(list)

    for caller in graph:

        for callee in graph[caller]:

            reverse[callee].append(
                caller
            )

    return reverse


# ============================================================
# 8. BFS IMPACT ANALYSIS
# ============================================================

def bfs(changed_functions, reverse):

    queue = deque()

    visited = set()

    impacted = []

    # Start from changed functions

    for function in changed_functions:

        if function not in visited:

            visited.add(function)

            queue.append(function)

    # BFS

    while queue:

        current = queue.popleft()

        impacted.append(current)

        # Find functions that depend on current

        for function in reverse[current]:

            if function not in visited:

                visited.add(function)

                queue.append(function)

    return impacted


# ============================================================
# 9. MAIN IMPACT ANALYSIS
# ============================================================

def impact_analysis(state: PR_State):

    simulated_merge = state.get(
        "simulated_merge",
        {}
    )

    # No simulated merge

    if not simulated_merge:

        return {
            "impact_analysis": {
                "success": False,
                "error": "Simulated merge not performed."
            }
        }

    # Merge conflict

    if simulated_merge.get(
        "merge_conflict",
        False
    ):

        return {
            "impact_analysis": {
                "success": False,
                "skipped": True,
                "reason": "Merge conflict detected."
            }
        }

    worktree = simulated_merge.get(
        "worktree"
    )

    if not worktree:

        return {
            "impact_analysis": {
                "success": False,
                "error": "Worktree not found."
            }
        }

    try:

        # ----------------------------------------------------
        # STEP 1: Find changed functions
        # ----------------------------------------------------

        changed_functions = []

        parsed_data = state.get(
            "parsed_data",
            []
        )

        file_code = state.get(
            "file_code",
            []
        )

        for file in parsed_data:

            filename = file.get(
                "filename"
            )

            patch = file.get(
                "patch",
                ""
            )

            changed_lines = get_changed_lines(
                patch
            )

            # Find code for this file

            code = ""

            for item in file_code:

                if item.get(
                    "filename"
                ) == filename:

                    code = item.get(
                        "code",
                        ""
                    )

                    break

            if not code:
                continue

            functions = find_changed_functions(
                code,
                changed_lines
            )

            for function in functions:

                changed_functions.append({

                    "filename": filename,

                    "function": function["name"],

                    "start": function["start"],

                    "end": function["end"],

                    "changed_lines": changed_lines

                })

        # ----------------------------------------------------
        # STEP 2: Build graph from whole merged repository
        # ----------------------------------------------------

        graph, all_functions = build_call_graph(
            worktree
        )

        # ----------------------------------------------------
        # STEP 3: Resolve function names
        # ----------------------------------------------------

        graph = resolve_graph(
            graph,
            all_functions
        )

        # ----------------------------------------------------
        # STEP 4: Reverse graph
        # ----------------------------------------------------

        reverse = reverse_graph(
            graph
        )

        # ----------------------------------------------------
        # STEP 5: Get graph IDs of changed functions
        # ----------------------------------------------------

        changed_ids = []

        for function in changed_functions:

            function_id = (
                function["filename"],
                function["function"]
            )

            if function_id in all_functions:

                changed_ids.append(
                    function_id
                )

        # ----------------------------------------------------
        # STEP 6: BFS
        # ----------------------------------------------------

        impacted_ids = bfs(
            changed_ids,
            reverse
        )

        # ----------------------------------------------------
        # STEP 7: Convert IDs into readable output
        # ----------------------------------------------------

        impacted_functions = []

        for function_id in impacted_ids:

            info = all_functions.get(
                function_id
            )

            if info:

                impacted_functions.append(
                    info
                )

        # ----------------------------------------------------
        # STEP 8: Return result
        # ----------------------------------------------------

        return {

            "impact_analysis": {

                "success": True,

                "changed_functions":
                    changed_functions,

                "impacted_functions":
                    impacted_functions,

                "changed_function_count":
                    len(changed_functions),

                "impacted_function_count":
                    len(impacted_functions)

            }

        }

    except Exception as e:

        return {

            "impact_analysis": {

                "success": False,

                "error": str(e)

            }

        }