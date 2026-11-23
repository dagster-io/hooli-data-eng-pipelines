from hooli_agents import snippet_check

BAD = """What we saw
```diff
- from dagster.components import load_defs
+ from dagster.components import load_from_defs_folder

-     load_defs(hooli_data_eng.defs),
+     load_from_defs_folder(hooli_data_eng.defs),
```
"""

GOOD = """```python
import dagster as dg

@dg.asset_check(asset="orders")
def orders_not_empty(context):
    return dg.AssetCheckResult(passed=True)

defs = dg.load_from_defs_folder(project_root=None)
```
"""


def test_wrong_call_signature_is_found():
    problems = snippet_check.problems_in(BAD)
    assert any("load_from_defs_folder" in p and "does not accept" in p for p in problems)


def test_sound_snippet_has_no_problems():
    assert snippet_check.problems_in(GOOD) == []


def test_missing_names_are_found():
    assert snippet_check.problems_in("```python\nfrom dagster import not_a_real_thing\n```")
    assert snippet_check.problems_in("```python\nimport dagster as dg\ndg.not_a_real_thing()\n```")


def test_other_code_and_prose_are_ignored():
    assert snippet_check.problems_in("```sql\nselect 1\n```\nplain text") == []
    assert snippet_check.problems_in("```python\nimport pandas as pd\npd.DataFrame(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)\n```") == []


def test_fragment_with_valid_imports_is_accepted():
    assert snippet_check.problems_in("```python\nfrom dagster import asset\n\n@asset(\n    ...\n```") == []
