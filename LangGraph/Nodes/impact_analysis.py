import os
import ast

from collections import defaultdict, deque

from unidiff import PatchSet

from workFlow import PR_State


def get_changed_lines(patch):

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


def get_functions(code):

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


def find_changed_functions(
    code,
    changed_lines
):

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


def get_called_functions(function_node):

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


def build_call_graph(worktree):

    graph = defaultdict(list)

    functions = {}

    for root, dirs, files in os.walk(worktree):

        dirs[:] = [
            d
            for d in dirs
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

                    "filename":
                        relative_path,

                    "function":
                        function_name,

                    "start":
                        node.lineno,

                    "end":
                        node.end_lineno
                }

                called_functions = (
                    get_called_functions(node)
                )

                for called in called_functions:

                    graph[function_id].append(
                        called
                    )

    return graph, functions


def resolve_graph(
    graph,
    functions
):

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
                name_to_functions[
                    called_name
                ]
            )

            for function in possible_functions:

                new_graph[caller].append(
                    function
                )

    return new_graph


def reverse_graph(graph):

    reverse = defaultdict(list)

    for caller in graph:

        for callee in graph[caller]:

            reverse[callee].append(
                caller
            )

    return reverse


def bfs(
    changed_functions,
    reverse
):

    queue = deque()

    visited = set()

    impacted = []

    for function in changed_functions:

        if function not in visited:

            visited.add(function)

            queue.append(function)

    while queue:

        current = queue.popleft()

        impacted.append(current)

        for function in reverse[current]:

            if function not in visited:

                visited.add(function)

                queue.append(function)

    return impacted


def impact_analysis(
    state: PR_State
):

    simulated_merge = state.get(
        "simulated_merge",
        {}
    )

    if not simulated_merge:

        return {
            "impact_analysis": {
                "success": False,
                "error":
                    "Simulated merge not performed."
            }
        }

    if simulated_merge.get(
        "merge_conflict",
        False
    ):

        return {
            "impact_analysis": {
                "success": False,
                "skipped": True,
                "reason":
                    "Merge conflict detected."
            }
        }

    worktree = simulated_merge.get(
        "worktree"
    )

    if not worktree:

        return {
            "impact_analysis": {
                "success": False,
                "error":
                    "Worktree not found."
            }
        }

    try:

        changed_functions = []

        parsed_data = state.get(
            "parsed_data",
            []
        )

        file_code = state.get(
            "file_code",
            []
        )

        # =====================================================
        # FIND CHANGED FUNCTIONS
        # =====================================================

        for file in parsed_data:

            filename = file.get(
                "filename"
            )

            patch = file.get(
                "patch",
                ""
            )

            changed_lines = (
                get_changed_lines(
                    patch
                )
            )

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

            functions = (
                find_changed_functions(
                    code,
                    changed_lines
                )
            )

            for function in functions:

                changed_functions.append({

                    "filename":
                        filename,

                    "function":
                        function["name"],

                    "start":
                        function["start"],

                    "end":
                        function["end"],

                    "changed_lines":
                        changed_lines
                })

        # =====================================================
        # BUILD CALL GRAPH
        # =====================================================

        graph, all_functions = (
            build_call_graph(
                worktree
            )
        )

        graph = resolve_graph(
            graph,
            all_functions
        )

        reverse = reverse_graph(
            graph
        )

        # =====================================================
        # FIND CHANGED FUNCTION IDS
        # =====================================================

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

        # =====================================================
        # BFS
        # =====================================================

        impacted_ids = bfs(
            changed_ids,
            reverse
        )

        # =====================================================
        # BUILD IMPACTED FUNCTION DATA
        # =====================================================

        impacted_functions = []

        for function_id in impacted_ids:

            info = all_functions.get(
                function_id
            )

            if info:

                impacted_functions.append(
                    info
                )

        # =====================================================
        # NEW:
        # ADD DIRECT CALLERS TO CHANGED FUNCTIONS
        # =====================================================

        for changed_function in changed_functions:

            changed_id = (
                changed_function["filename"],
                changed_function["function"]
            )

            direct_callers = []

            for caller_id in reverse.get(
                changed_id,
                []
            ):

                caller_info = all_functions.get(
                    caller_id
                )

                if caller_info:

                    direct_callers.append(
                        caller_info
                    )

            changed_function[
                "direct_callers"
            ] = direct_callers

        # =====================================================
        # RETURN IMPACT ANALYSIS
        # =====================================================

        return {

            "impact_analysis": {

                "success":
                    True,

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

                "success":
                    False,

                "error":
                    str(e)
            }
        }