{% macro day_diff_from_run(start) %}
    DATEDIFF(
        day,
        {{start}}::number::timestamp,
        current_date()
    )
{% endmacro %}
