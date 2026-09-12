import os
import ast
import subprocess

from huggingface_hub import InferenceClient

from workFlow import PR_State


MODEL_NAME = "boraoxkan/codereview-ai"


client = InferenceClient(
    api_key=os.environ["HF_TOKEN"]
)


# ============================================================
# 1. AST: Extract function signature
# ============================================================

def get_function_signature(
    code,
    function_name
):

    try:

        tree = ast.parse(code)

    except SyntaxError:

        return None

    for node in ast.walk(tree):

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef
            )
        ):

            if node.name != function_name:
                continue

            args = node.args

            positional = (
                args.posonlyargs +
                args.args
            )

            required_count = (
                len(positional) -
                len(args.defaults)
            )

            required_params = [
                arg.arg
                for arg in positional[
                    :required_count
                ]
            ]

            optional_params = [
                arg.arg
                for arg in positional[
                    required_count:
                ]
            ]

            keyword_only = [
                arg.arg
                for arg in args.kwonlyargs
            ]

            return_type = None

            if node.returns:

                return_type = ast.unparse(
                    node.returns
                )

            return {

                "parameters": [
                    arg.arg
                    for arg in positional
                ],

                "required_parameters":
                    required_params,

                "optional_parameters":
                    optional_params,

                "keyword_only_parameters":
                    keyword_only,

                "has_args":
                    args.vararg is not None,

                "has_kwargs":
                    args.kwarg is not None,

                "return_type":
                    return_type
            }

    return None


# ============================================================
# 2. AST: Check whether function interface changed
# ============================================================

def check_function_change(
    old_code,
    new_code,
    function_name
):

    old_signature = (
        get_function_signature(
            old_code,
            function_name
        )
    )

    new_signature = (
        get_function_signature(
            new_code,
            function_name
        )
    )

    if (
        old_signature is None
        or
        new_signature is None
    ):

        return {

            "changed":
                True,

            "reason":
                "Could not determine function signature."
        }

    changes = []

    if (
        old_signature["parameters"]
        !=
        new_signature["parameters"]
    ):

        changes.append(
            "parameters changed"
        )

    if (
        old_signature["required_parameters"]
        !=
        new_signature["required_parameters"]
    ):

        changes.append(
            "required parameters changed"
        )

    if (
        old_signature["keyword_only_parameters"]
        !=
        new_signature["keyword_only_parameters"]
    ):

        changes.append(
            "keyword-only parameters changed"
        )

    if (
        old_signature["has_args"]
        !=
        new_signature["has_args"]
    ):

        changes.append(
            "*args changed"
        )

    if (
        old_signature["has_kwargs"]
        !=
        new_signature["has_kwargs"]
    ):

        changes.append(
            "**kwargs changed"
        )

    if (
        old_signature["return_type"]
        !=
        new_signature["return_type"]
    ):

        changes.append(
            "return type changed"
        )

    return {

        "changed":
            len(changes) > 0,

        "changes":
            changes,

        "old_signature":
            old_signature,

        "new_signature":
            new_signature
    }


# ============================================================
# 3. AST: Find calls
# ============================================================

def find_function_calls(
    caller_code,
    function_name
):

    try:

        tree = ast.parse(
            caller_code
        )

    except SyntaxError:

        return []

    calls = []

    for node in ast.walk(tree):

        if not isinstance(
            node,
            ast.Call
        ):
            continue

        called_name = None

        if isinstance(
            node.func,
            ast.Name
        ):

            called_name = (
                node.func.id
            )

        elif isinstance(
            node.func,
            ast.Attribute
        ):

            called_name = (
                node.func.attr
            )

        if called_name != function_name:
            continue

        calls.append({

            "line":
                node.lineno,

            "end_line":
                node.end_lineno,

            "positional_args":
                len(node.args),

            "keyword_args": [

                keyword.arg

                for keyword in node.keywords

                if keyword.arg is not None
            ]
        })

    return calls


# ============================================================
# 4. AST: Check caller compatibility
# ============================================================

def check_caller_compatibility(
    caller_code,
    function_name,
    new_signature
):

    calls = find_function_calls(
        caller_code,
        function_name
    )

    if not calls:

        return {

            "found":
                False,

            "compatible":
                True,

            "reason":
                "No call to changed function found."
        }

    problems = []

    required_count = len(
        new_signature[
            "required_parameters"
        ]
    )

    total_count = len(
        new_signature[
            "parameters"
        ]
    )

    allowed_keywords = set(

        new_signature["parameters"]

        +
        new_signature[
            "keyword_only_parameters"
        ]
    )

    for call in calls:

        positional_count = (
            call["positional_args"]
        )

        # ------------------------------------
        # Too few arguments
        # ------------------------------------

        if (
            positional_count
            <
            required_count
        ):

            problems.append({

                "type":
                    "ARGUMENT_MISMATCH",

                "line":
                    call["line"],

                "reason":
                    f"Function now requires at least "
                    f"{required_count} positional "
                    f"arguments, but caller provides "
                    f"{positional_count}."
            })

        # ------------------------------------
        # Too many arguments
        # ------------------------------------

        if (
            positional_count
            >
            total_count
            and
            not new_signature["has_args"]
        ):

            problems.append({

                "type":
                    "ARGUMENT_MISMATCH",

                "line":
                    call["line"],

                "reason":
                    f"Function accepts at most "
                    f"{total_count} positional "
                    f"arguments, but caller provides "
                    f"{positional_count}."
            })

        # ------------------------------------
        # Invalid keyword arguments
        # ------------------------------------

        for keyword in call[
            "keyword_args"
        ]:

            if (
                keyword not in allowed_keywords
                and
                not new_signature["has_kwargs"]
            ):

                problems.append({

                    "type":
                        "KEYWORD_ARGUMENT_MISMATCH",

                    "line":
                        call["line"],

                    "reason":
                        f"Caller uses keyword "
                        f"'{keyword}', but the new "
                        f"function does not accept it."
                })

    return {

        "found":
            True,

        "compatible":
            len(problems) == 0,

        "problems":
            problems,

        "calls":
            calls
    }


# ============================================================
# 5. Extract function
# ============================================================

def extract_function(
    code,
    function_name
):

    try:

        tree = ast.parse(
            code
        )

    except SyntaxError:

        return ""

    lines = code.splitlines()

    for node in ast.walk(tree):

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef
            )
        ):

            if node.name != function_name:
                continue

            start = node.lineno - 1
            end = node.end_lineno

            return "\n".join(
                lines[start:end]
            )

    return ""


# ============================================================
# 6. Tier 3: LLM
# ============================================================

def llm_check_impact(
    changed_function,
    caller_function,
    function_name
):

    prompt = f"""
You are reviewing the impact of a changed Python function.

Changed function:
{changed_function}

Caller function:
{caller_function}

The caller uses the function:
{function_name}

Determine whether the change can break the caller even if
the function signature and arguments appear compatible.

Check specifically:

1. Return value meaning
2. Return structure/type
3. Exceptions
4. Side effects
5. Important assumptions made by the caller
6. Changed behavior that can make the caller incorrect

Return exactly:

Impact: YES or NO
Severity: LOW, MEDIUM, or HIGH
Reason: <short explanation>
Suggested fix: <short suggestion>
"""

    try:

        response = client.chat.completions.create(

            model=MODEL_NAME,

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            max_tokens=300,

            temperature=0
        )

        return (
            response
            .choices[0]
            .message
            .content
        )

    except Exception as e:

        return (
            f"LLM check failed: {str(e)}"
        )


# ============================================================
# 7. Three-tier verifier for ONE caller
# ============================================================

def verify_function_impact(
    old_code,
    new_code,
    function_name,
    caller_code,
    caller_function_name
):

    result = {

        "function":
            function_name,

        "caller":
            caller_function_name,

        "impact":
            False,

        "tier1": {},
        "tier2": {},
        "tier3": {}
    }

    # ========================================================
    # TIER 1
    # ========================================================

    tier1 = check_function_change(

        old_code,
        new_code,
        function_name
    )

    result["tier1"] = tier1

    if not tier1["changed"]:

        result["impact"] = False

        result["reason"] = (
            "Function interface did not change."
        )

        return result

    # ========================================================
    # TIER 2
    # ========================================================

    tier2 = check_caller_compatibility(

        caller_code,
        function_name,
        tier1["new_signature"]
    )

    result["tier2"] = tier2

    if not tier2["compatible"]:

        result["impact"] = True

        result["reason"] = (
            "Caller is incompatible with "
            "the new function interface."
        )

        return result

    # ========================================================
    # TIER 3
    # ========================================================

    changed_function = extract_function(

        new_code,
        function_name
    )

    caller_function = extract_function(

        caller_code,
        caller_function_name
    )

    llm_result = llm_check_impact(

        changed_function,

        caller_function,

        function_name
    )

    result["tier3"] = {

        "analysis":
            llm_result
    }

    if (
        "impact: yes"
        in
        llm_result.lower()
    ):

        result["impact"] = True

        result["reason"] = (
            "LLM detected a possible semantic "
            "or behavioral impact."
        )

    else:

        result["impact"] = False

        result["reason"] = (
            "No definite caller impact detected."
        )

    return result


# ============================================================
# 8. Read new code from simulated merge worktree
# ============================================================

def read_new_file(
    worktree,
    filename
):

    path = os.path.join(
        worktree,
        filename
    )

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()

    except Exception:

        return ""


# ============================================================
# 9. Read OLD code from target branch
# ============================================================

def read_old_file(
    worktree,
    target_branch,
    filename
):

    try:

        result = subprocess.run(

            [
                "git",
                "-C",
                worktree,
                "show",
                f"{target_branch}:{filename}"
            ],

            capture_output=True,

            text=True,

            check=True
        )

        return result.stdout

    except Exception:

        return ""


# ============================================================
# 10. LANGGRAPH NODE
# ============================================================

def impact_verifier(
    state: PR_State
):

    # ========================================================
    # GET IMPACT ANALYSIS RESULT FROM STATE
    # ========================================================

    impact_data = state.get(
        "impact_analysis",
        {}
    )

    if not impact_data.get(
        "success",
        False
    ):

        return {
            "verification_results": []
        }

    changed_functions = (
        impact_data.get(
            "changed_functions",
            []
        )
    )

    if not changed_functions:

        return {
            "verification_results": []
        }

    # ========================================================
    # GET SIMULATED MERGE FROM STATE
    # ========================================================

    simulated_merge = state.get(
        "simulated_merge",
        {}
    )

    worktree = simulated_merge.get(
        "worktree"
    )

    if not worktree:

        return {
            "verification_results": []
        }

    # ========================================================
    # GET TARGET BRANCH FROM STATE
    # ========================================================

    target_branch = state.get(
        "target_branch"
    )

    if not target_branch:

        target_branch = (
            simulated_merge.get(
                "target_branch"
            )
        )

    if not target_branch:

        return {
            "verification_results": []
        }

    verification_results = []

    # ========================================================
    # LOOP THROUGH CHANGED FUNCTIONS
    # ========================================================

    for changed_function in changed_functions:

        changed_filename = (
            changed_function[
                "filename"
            ]
        )

        changed_name = (
            changed_function[
                "function"
            ]
        )

        # ----------------------------------------------------
        # DIRECT CALLERS WERE ALREADY FOUND BY
        # IMPACT ANALYSIS
        # ----------------------------------------------------

        direct_callers = (
            changed_function.get(
                "direct_callers",
                []
            )
        )

        if not direct_callers:
            continue

        # ====================================================
        # GET NEW VERSION OF CHANGED FILE
        # ====================================================

        new_code = read_new_file(

            worktree,

            changed_filename
        )

        if not new_code:
            continue

        # ====================================================
        # GET OLD VERSION OF CHANGED FILE
        # ====================================================

        old_code = read_old_file(

            worktree,

            target_branch,

            changed_filename
        )

        if not old_code:
            continue

        # ====================================================
        # VERIFY EVERY DIRECT CALLER
        # ====================================================

        for caller in direct_callers:

            caller_filename = (
                caller["filename"]
            )

            caller_name = (
                caller["function"]
            )

            # ----------------------------------------------
            # Get caller code from simulated merge
            # ----------------------------------------------

            caller_code = read_new_file(

                worktree,

                caller_filename
            )

            if not caller_code:
                continue

            # ----------------------------------------------
            # Perform 3-tier verification
            # ----------------------------------------------

            verification = (
                verify_function_impact(

                    old_code=old_code,

                    new_code=new_code,

                    function_name=changed_name,

                    caller_code=caller_code,

                    caller_function_name=caller_name
                )
            )

            verification_results.append({

                "changed_function": {

                    "filename":
                        changed_filename,

                    "function":
                        changed_name
                },

                "caller": {

                    "filename":
                        caller_filename,

                    "function":
                        caller_name
                },

                "verification":
                    verification
            })

    # ========================================================
    # RETURN STATE UPDATE
    # ========================================================

    return {

        "verification_results":
            verification_results
    }