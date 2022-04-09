from ...prelude import *
import altair as alt
from .model import Scenario


def get_records(scenario : Scenario):
    for project in scenario.projects:
        for role in project.roles:
            skill = scenario.skills[role.skill_id]
            staff = scenario.contributors.try_get(role.cont_id)
            
            record = dict(
                project = project.name,
                start_before = project.start_before,
                end_before = project.end_before,
                late = project.late,
                best_score = project.best_score,
                score = project.score,
                skill = skill.name,
                staff = staff.name if staff else '',
                role = f'{project.name} - {skill.name}',
                role_level = role.level,
                start = role.start,
                end = role.end,
                mid = (role.start + role.end) / 2.0, 
                days = project.days,
            )
            yield record



def plot_scenario(scenario : Scenario, solutions=[], width = 600):
    records = list(get_records(scenario))
    inline = alt.InlineData(name='data', values=records)
    frame = DF.from_records(records)
    print(frame)

    base = alt.Chart(inline)
   
    roster_chart = (
        base
        .encode(x = alt.X(
            field = 'start',
            type  = 'quantitative',
            title = 'Day',
            axis = alt.Axis(
                bandPosition=0.5
            )
            ))
        .encode(x2 = 'end:Q')
        .encode(y = 'staff:N')
        .encode(color = 'project:N')
        .encode(tooltip=[
            'project:N',
            'start_before:Q',
            'end_before:Q',
            'start:Q',
            'end:Q',
            'days:Q',
            'late:Q',
            'best_score:Q',
            'score:Q',
            'skill:N',
            'staff:N',
            'role_level:Q'
            ])
        .mark_bar(opacity=0.8)
    )
        
    roster_labels = (
        base
        .encode(x = 'mid:Q')
        .encode(y = 'staff:N')
        .mark_text(align = 'center', baseline='middle')
        .encode(text = 'text:N')
        .transform_calculate(text = 'datum.skill + " - " + datum.role_level')
    )
    
    late_lines = (
        base
        .encode(x = 'start_before:Q')
        .encode(x2 = 'start:Q')
        .encode(y = 'staff:N')
        .encode(color = 'project:N')
        .mark_line(point=True)
        .encode(size=alt.value(2))
        .encode(opacity=alt.value(0.3))
        .transform_filter(datum.late > 0)
    )
    
    chart = (alt
        .layer(
            roster_chart,
            roster_labels,
            late_lines
            )
        .properties(
            title=scenario.name,
            height=400,
            width=width
        )
    )

    return chart