"""
Solve the scenario using a static minizinc model with 
data passed through as a dzn file.
"""

from unconstrained import *
from .model import *

model_string = """
% ==== Google Hash Code 2022 =====================================================

include "int_set_channel.mzn";
include "diffn.mzn";

int: max_score;
int: max_skill;
int: max_day;
int: max_proj;
int: max_cont;
int: max_role;

par set of int: SCORE = 0..max_score;
par set of int: LEVEL = 0..100;
par set of int: SKILL = 1..max_skill;
par set of int: DAY = 0..max_day;
par set of int: PROJECT = 1..max_proj;
par set of int: CONTRIBUTOR = 1..max_cont;
par set of int: ROLE = 1..max_role;

% ==== Projects ==================================================================

array[PROJECT] of var DAY: project_start;
array[PROJECT] of par DAY: project_duration;
array[PROJECT] of var DAY: project_end; constraint project_end = [project_start[p] + project_duration[p] | p in PROJECT];
array[PROJECT] of var DAY: project_late; constraint project_late = [max(project_end[p] - project_end_before[p], 0) | p in PROJECT];
array[PROJECT] of par DAY: project_end_before;
array[PROJECT] of par SCORE: project_best_score;
array[PROJECT] of var SCORE: project_score; constraint project_score = [max(project_best_score[p] - project_late[p], 0) | p in PROJECT];
array[PROJECT, CONTRIBUTOR] of var bool: project_contributor;

% ==== Roles =====================================================================

array[ROLE] of par PROJECT: role_project;

% Skill required for each role
array[ROLE] of par SKILL: role_skill;

% Minimum level required for each role
array[ROLE] of par LEVEL: role_level;

% Contributor assigned to each role
array[ROLE] of var CONTRIBUTOR: role_contributor;

% Mentor (optional) for each role
array[ROLE] of var opt CONTRIBUTOR: role_mentor;

% Did the contributor progress from this role?
array[ROLE] of var bool: role_progress;

% ==== Contributors ==============================================================

array[CONTRIBUTOR, SKILL] of par LEVEL: contributor_skill;
array[CONTRIBUTOR] of var set of ROLE: contributor_roles;

% ==== Constraints ===============================================================

function var LEVEL: get_level(var ROLE: r) =
    let {
                        
    var SKILL : s = role_skill[r];
    var PROJECT: p = role_project[r];
    var CONTRIBUTOR: c = role_contributor[r];
    var LEVEL : base = contributor_skill[c, s];
                
    var LEVEL : progress = 
        sum (r2 in contributor_roles[c]) (                   
            % Different role
            (r != r2)
            /\\
            % Same skill
            (role_skill[r2] = s)
            /\\
            % Project Before this
            (project_end[role_project[r2]] <= project_start[p])
            /\\
            % Progressed from role
            role_progress[r2]
            )
            ;
    }
    in
    base + progress
;

% Contributors satisfy the skill requirements for the roles
constraint forall (r in ROLE) (
    let {
        par PROJECT : p    = role_project[r];
        par SKILL   : s    = role_skill[r];
        par LEVEL   : l    = role_level[r];
        var CONTRIBUTOR: c = role_contributor[r];
    }
    in
    % Contributor meets requirements
    (
        get_level(r) >= l
        /\\
        absent(role_mentor[r])
    )
    \\/
    % Mentor exists
    (
        let {
            var ROLE: r_m;
            var CONTRIBUTOR: c_m = role_contributor[r_m];
            var SKILL : s_m = role_skill[r_m];
        }
        in
        r_m != r
        /\\
        c_m != c
        /\\
        s_m = s
        /\\
        get_level(r) = (l - 1)
        /\\
        get_level(r_m) >= l
    )        
)
;

% Int Set Channel
constraint int_set_channel(role_contributor, contributor_roles);

% Contributors can only work on 1 role at a time
constraint diffn(
    [project_start[role_project[r]] | r in ROLE],
    role_contributor,
    [project_duration[role_project[r]] | r in ROLE],
    [1 | r in ROLE]
)
;

solve maximize sum(project_score);
"""

async def solve_with_static_minizinc(scenario : Scenario, options : MiniZincOptions):

    max_skill = scenario.skills.count
    max_proj  = scenario.projects.count
    max_role  = scenario.roles.count
    max_cont  = scenario.contributors.count
    max_score = scenario.projects.max('best_score')
    max_day   = scenario.projects.sum('days') + 1

    project_duration   = [p.days for p in scenario.projects]
    project_end_before = [p.end_before for p in scenario.projects]
    project_best_score = [p.best_score for p in scenario.projects]

    role_project = [r.proj_id for r in scenario.roles]
    role_skill   = [r.skill_id for r in scenario.roles]
    role_level   = [r.level for r in scenario.roles]
    
    contributor_skill = [c.competencies.get(s, 0) for c in scenario.contributors for s in scenario.skills.keys]
    
    async for result in solve_minizinc_model(
        model_string,
        options,
        name = scenario.name,
        max_skill=max_skill,
        max_proj=max_proj,
        max_role=max_role,
        max_cont=max_cont,
        max_score=max_score,
        max_day=max_day,
        project_duration=project_duration,
        project_end_before=project_end_before,
        project_best_score=project_best_score,
        role_project=role_project,
        role_skill=role_skill,
        role_level=role_level,
        contributor_skill=contributor_skill
        ):
                        
        if not result.status.has_solution:
            log.error(f'"{result.name}" failed with status "{result.status}"')
            continue

        for contributor in scenario.contributors:
            i = contributor.cont_id - 1
            contributor.roles = Roles()
            contributor.projects = Projects()
               
                
        for project in scenario.projects:
            i = project.proj_id - 1
                                    
            project.staff = Contributors()
            project.start = result['project_start', i]
            project.end   = result['project_end', i]
            project.score = result['project_score', i]
            project.late  = result['project_late', i]
            project.score = result['project_score', i]
                                                                                                            
            for role in project.roles:
                i = role.role_id - 1

                role.start     = project.start
                role.end       = project.end
                role.cont_id   = result['role_contributor',i]
                role.mentor_id = result['role_mentor',i] or 0
                role.mentor    = scenario.contributors.try_get(role.mentor_id)
                role.staff     = scenario.contributors[role.cont_id]
                
                role.staff.roles += role
                role.staff.projects += project
                project.staff += role.staff


        yield result
