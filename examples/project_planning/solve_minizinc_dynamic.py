"""
Solve the scenario using a dynamically generated minizinc model
"""

from unconstrained import *
from .model import *

async def solve_with_dynamic_minizinc(scenario : Scenario, options : SolveOptions):
                                        
    max_score = scenario.projects.max('best_score')
    max_day = scenario.projects.sum('days') + 1
                                                                
    model = MiniZincModelBuilder()
    
    model.add_section(
        f"Google Hash Code 2022 - {scenario.name}"
    )
                
    model.add_global(
        'int_set_channel',
        'diffn'
    )
        
    model.add_set(
        name  = 'SCORE',
        type  = 'int',
        min   = 0,
        max   = max_score,
    )

    model.add_set(
        name = 'LEVEL',
        type = 'int',
        min  = 0,
        max  = 100,
    )
    
    model.add_set(
        name = 'SKILL',
        type = 'int',
        max  = scenario.skills.count        
    )
                    
    model.add_set(
        name = 'DAY',
        type = 'int',
        min  = 0,
        max  = max_day,
    )
                
    model.add_set(
        name = 'PROJECT',
        type = 'int',
        max  = scenario.projects.count,
    )
            
    model.add_set(
        name = 'CONTRIBUTOR',
        type = 'int',
        max  = scenario.contributors.count
    )

    model.add_set(
        name = 'ROLE',
        type = 'int',
        max  = scenario.roles.count
    )

    model.add_section('Projects')
    
    model.add_array(
        name  = 'project_start',
        index = 'PROJECT',
        type  = 'DAY',
        inst  = VAR
    )
    
    model.add_array(
        name  = 'project_duration',
        index = 'PROJECT',
        type  = 'DAY',
        inst  = PAR,
        value = [p.days for p in scenario.projects]
    )

    model.add_array(
        name  = 'project_end',
        index = 'PROJECT',
        type  = 'DAY',
        inst  = VAR,
        value = '[project_start[p] + project_duration[p] | p in PROJECT]',
        inline = False
    )

    model.add_array(
        name  = 'project_late',
        index = 'PROJECT',
        type  = 'DAY',
        inst  = VAR,
        value = '[max(project_end[p] - project_end_before[p], 0) | p in PROJECT]',
        inline = False
    )
        
    model.add_array(
        name  = 'project_end_before',
        index = 'PROJECT',
        type  = 'DAY',
        inst  = PAR,
        value = [p.end_before for p in scenario.projects]
    )
            
    model.add_array(
        name  = 'project_best_score',
        index = 'PROJECT',
        type  = 'SCORE',
        inst  = PAR,
        value = [p.best_score for p in scenario.projects]
    )
            
    model.add_array(
        name  = 'project_score',
        index = 'PROJECT',
        type  = 'SCORE',
        inst  = VAR,
        inline = False,
        value = f'[max(project_best_score[p] - project_late[p], 0) | p in PROJECT]'
    )
                            
    model.add_array(
        name   = 'project_contributor',
        index  = 'PROJECT',
        index2 = 'CONTRIBUTOR',
        type   = 'bool',
        inst   = VAR,
    )
                
    model.add_section('Roles')
    
    model.add_array(
        name  = 'role_project',
        index = 'ROLE',
        type  = 'PROJECT',
        value = [r.proj_id for r in scenario.roles]
    )
        
    model.add_array(
        name  = 'role_skill',
        index = 'ROLE',
        type  = 'SKILL',
        value = [r.skill_id for r in scenario.roles],
        comment = 'Skill required for each role'
    )

    model.add_array(
        name  = 'role_level',
        index = 'ROLE',
        type  = 'LEVEL',
        value = [r.level for r in scenario.roles],
        comment = 'Minimum level required for each role'
    )
                        
    model.add_array(
        name  = 'role_contributor',
        index = 'ROLE',
        type  = 'CONTRIBUTOR',
        inst  = VAR,
        comment = 'Contributor assigned to each role'
    )
    
    model.add_array(
        name  = 'role_mentor',
        index = 'ROLE',
        type  = 'opt CONTRIBUTOR',
        inst  = VAR,
        comment = 'Mentor (optional) for each role'
    )

    model.add_array(
        name  = 'role_progress',
        index = 'ROLE',
        type  = 'bool',
        inst  = VAR,
        comment = 'Did the contributor progress from this role?'
    )
            
    model.add_section('Contributors')

    model.add_array(
        name   = 'contributor_skill',
        index  = 'CONTRIBUTOR',
        index2 = 'SKILL',
        type   = 'LEVEL',
        inst   = PAR,
        verbose = True,                
        value  = [c.competencies.get(s, 0) for c in scenario.contributors for s in scenario.skills.keys]
    )

    model.add_array(
        name = 'contributor_roles',
        index = 'CONTRIBUTOR',
        type  = 'set of ROLE',
        inst  = VAR        
    )
       
    model.add_section('Constraints')
    
    model.add_expression('''
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
    ''')
            
    model.add_constraint(
        'Contributors satisfy the skill requirements for the roles',
        """
        forall (r in ROLE) (

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
        """)

    model.add_constraint(
        'Int Set Channel',
        'int_set_channel(role_contributor, contributor_roles)'
    )
            
    model.add_constraint(
        'Contributors can only work on 1 role at a time',
        '''
        diffn(
        [project_start[role_project[r]] | r in ROLE],
        role_contributor,
        [project_duration[role_project[r]] | r in ROLE],
        [1 | r in ROLE]
        )
        '''
    )
        

    model.add_expression(
        f'solve maximize sum(project_score)'
    )
        

    async for result in solve(model.string, options, name = scenario.name):
                
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