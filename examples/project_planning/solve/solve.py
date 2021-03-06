
# async def solve_with_dynamic_minizinc(scenario : Scenario, options : SolveOptions):
                                                
#     max_score = max(p.best_score for p in scenario.projects)
#     max_day = sum(p.days for p in scenario.projects) + 1
                                                                    
#     model = MiniZincModelBuilder()
    
#     model.add_section(
#         f"Google Hash Code 2022 - {scenario.name}"
#     )
                
#     model.add_global(
#         'int_set_channel',
#         'diffn'
#     )
        
#     model.add_set(
#         name  = 'SCORE',
#         type  = 'int',
#         min   = 0,
#         max   = max_score,
#     )

#     model.add_set(
#         name = 'LEVEL',
#         type = 'int',
#         min  = 0,
#         max  = 100,
#     )
    
#     model.add_set(
#         name = 'SKILL',
#         type = 'int',
#         max  = len(scenario.skills)
#     )
                    
#     model.add_set(
#         name = 'DAY',
#         type = 'int',
#         min  = 0,
#         max  = max_day,
#     )
                
#     model.add_set(
#         name = 'PROJECT',
#         type = 'int',
#         max  = len(scenario.projects),
#     )
            
#     model.add_set(
#         name = 'CONTRIBUTOR',
#         type = 'int',
#         max  = len(scenario.contributors)
#     )

#     model.add_set(
#         name = 'ROLE',
#         type = 'int',
#         max  = len([1 for p in scenario.projects for r in p.roles])
#     )

#     model.add_section('Projects')
    
#     model.add_array(
#         name  = 'project_start',
#         index = 'PROJECT',
#         type  = 'DAY',
#         inst  = VAR
#     )
    
#     model.add_array(
#         name  = 'project_duration',
#         index = 'PROJECT',
#         type  = 'DAY',
#         inst  = PAR,
#         value = [p.days for p in scenario.projects]
#     )

#     model.add_array(
#         name  = 'project_end',
#         index = 'PROJECT',
#         type  = 'DAY',
#         inst  = VAR,
#         value = '[project_start[p] + project_duration[p] | p in PROJECT]',
#         inline = False
#     )

#     model.add_array(
#         name  = 'project_late',
#         index = 'PROJECT',
#         type  = 'DAY',
#         inst  = VAR,
#         value = '[max(project_end[p] - project_end_before[p], 0) | p in PROJECT]',
#         inline = False
#     )
        
#     model.add_array(
#         name  = 'project_end_before',
#         index = 'PROJECT',
#         type  = 'DAY',
#         inst  = PAR,
#         value = [p.end_before for p in scenario.projects]
#     )
            
#     model.add_array(
#         name  = 'project_best_score',
#         index = 'PROJECT',
#         type  = 'SCORE',
#         inst  = PAR,
#         value = [p.best_score for p in scenario.projects]
#     )
            
#     model.add_array(
#         name  = 'project_score',
#         index = 'PROJECT',
#         type  = 'SCORE',
#         inst  = VAR,
#         inline = False,
#         value = f'[max(project_best_score[p] - project_late[p], 0) | p in PROJECT]'
#     )
                            
#     model.add_array(
#         name   = 'project_contributor',
#         index  = 'PROJECT',
#         index2 = 'CONTRIBUTOR',
#         type   = 'bool',
#         inst   = VAR,
#     )
                
#     model.add_section('Roles')
    
#     model.add_array(
#         name  = 'role_project',
#         index = 'ROLE',
#         type  = 'PROJECT',
#         value = [r.project.id for p in scenario.projects for r in p.roles]
#     )
        
#     model.add_array(
#         name  = 'role_skill',
#         index = 'ROLE',
#         type  = 'SKILL',
#         value = [r.skill_id for p in scenario.projects for r in p.roles],
#         comment = 'Skill required for each role'
#     )

#     model.add_array(
#         name  = 'role_level',
#         index = 'ROLE',
#         type  = 'LEVEL',
#         value = [r.level for p in scenario.projects for r in p.roles],
#         comment = 'Minimum level required for each role'
#     )
                        
#     model.add_array(
#         name  = 'role_contributor',
#         index = 'ROLE',
#         type  = 'CONTRIBUTOR',
#         inst  = VAR,
#         comment = 'Contributor assigned to each role'
#     )
    
#     model.add_array(
#         name  = 'role_mentor',
#         index = 'ROLE',
#         type  = 'opt CONTRIBUTOR',
#         inst  = VAR,
#         comment = 'Mentor (optional) for each role'
#     )

#     model.add_array(
#         name  = 'role_progress',
#         index = 'ROLE',
#         type  = 'bool',
#         inst  = VAR,
#         comment = 'Did the contributor progress from this role?'
#     )
            
#     model.add_section('Contributors')

#     model.add_array(
#         name   = 'contributor_skill',
#         index  = 'CONTRIBUTOR',
#         index2 = 'SKILL',
#         type   = 'LEVEL',
#         inst   = PAR,
#         verbose = True,                
#         value  = [c.competencies.get(s, 0) for c in scenario.contributors for s in scenario.skills.keys]
#     )

#     model.add_array(
#         name = 'contributor_roles',
#         index = 'CONTRIBUTOR',
#         type  = 'set of ROLE',
#         inst  = VAR        
#     )
       
#     model.add_section('Constraints')
    
#     model.add_expression('''
#         function var LEVEL: get_level(var ROLE: r) =
#             let {
                                
#             var SKILL : s = role_skill[r];
#             var PROJECT: p = role_project[r];
#             var CONTRIBUTOR: c = role_contributor[r];
#             var LEVEL : base = contributor_skill[c, s];
                        
#             var LEVEL : progress = 
#                 sum (r2 in contributor_roles[c]) (                   
#                     % Different role
#                     (r != r2)
#                     /\\
#                     % Same skill
#                     (role_skill[r2] = s)
#                     /\\
#                     % Project Before this
#                     (project_end[role_project[r2]] <= project_start[p])
#                     /\\
#                     % Progressed from role
#                     role_progress[r2]
#                     )
#                     ;
#             }
#             in
#             base + progress
#     ''')
            
#     model.add_constraint(
#         'Contributors satisfy the skill requirements for the roles',
#         """
#         forall (r in ROLE) (

#         let {
#             par PROJECT : p    = role_project[r];
#             par SKILL   : s    = role_skill[r];
#             par LEVEL   : l    = role_level[r];
#             var CONTRIBUTOR: c = role_contributor[r];
#         }
#         in
#         % Contributor meets requirements
#         (
#             get_level(r) >= l
#             /\\ 
#             absent(role_mentor[r])
#         )
#         \\/
#         % Mentor exists
#         (
#             let {
#                 var ROLE: r_m;
#                 var CONTRIBUTOR: c_m = role_contributor[r_m];
#                 var SKILL : s_m = role_skill[r_m];
#             }
#             in
#             r_m != r
#             /\\
#             c_m != c
#             /\\
#             s_m = s
#             /\\
#             get_level(r) = (l - 1)
#             /\\
#             get_level(r_m) >= l
#         )
        
#         )
#         """)

#     model.add_constraint(
#         'Int Set Channel',
#         'int_set_channel(role_contributor, contributor_roles)'
#     )
            
#     model.add_constraint(
#         'Contributors can only work on 1 role at a time',
#         '''
#         diffn(
#         [project_start[role_project[r]] | r in ROLE],
#         role_contributor,
#         [project_duration[role_project[r]] | r in ROLE],
#         [1 | r in ROLE]
#         )
#         '''
#     )
        

#     model.add_expression(
#         f'solve maximize sum(project_score)'
#     )
        

#     async for result in solutions(model.string, options, name = scenario.name):
                
#         if not result.status.has_solution:
#             log.error(f'"{result.name}" failed with status "{result.status}"')
#             continue

#         for contributor in scenario.contributors:
#             i = contributor.cont_id - 1
#             contributor.roles = Roles()
#             contributor.projects = Projects()
               
                
#         for project in scenario.projects:
#             i = project.proj_id - 1
                                    
#             project.staff = Contributors()
#             project.start = result['project_start', i]
#             project.end   = result['project_end', i]
#             project.score = result['project_score', i]
#             project.late  = result['project_late', i]
#             project.score = result['project_score', i]
                                                                                    
#             for role in project.roles:
#                 i = role.role_id - 1

#                 role.start     = project.start
#                 role.end       = project.end
#                 role.contributor_id   = result['role_contributor',i]
#                 role.mentor_id = result['role_mentor',i] or 0
#                 role.mentor    = scenario.contributors.try_get(role.mentor_id)
#                 role.staff     = scenario.contributors[role.contributor_id]
                
#                 role.staff.roles += role
#                 role.staff.projects += project
#                 project.staff += role.staff


#         yield result    



# async def solve_with_static_minizinc(scenario : Scenario, options : SolveOptions):

#     model_string = """
# % ==== Google Hash Code 2022 =====================================================

# include "int_set_channel.mzn";
# include "diffn.mzn";

# int: max_score;
# int: max_skill;
# int: max_day;
# int: max_proj;
# int: max_cont;
# int: max_role;

# par set of int: SCORE = 0..max_score;
# par set of int: LEVEL = 0..100;
# par set of int: SKILL = 1..max_skill;
# par set of int: DAY = 0..max_day;
# par set of int: PROJECT = 1..max_proj;
# par set of int: CONTRIBUTOR = 1..max_cont;
# par set of int: ROLE = 1..max_role;

# % ==== Projects ==================================================================

# array[PROJECT] of var DAY: project_start;
# array[PROJECT] of par DAY: project_duration;
# array[PROJECT] of var DAY: project_end; constraint project_end = [project_start[p] + project_duration[p] | p in PROJECT];
# array[PROJECT] of var DAY: project_late; constraint project_late = [max(project_end[p] - project_end_before[p], 0) | p in PROJECT];
# array[PROJECT] of par DAY: project_end_before;
# array[PROJECT] of par SCORE: project_best_score;
# array[PROJECT] of var SCORE: project_score; constraint project_score = [max(project_best_score[p] - project_late[p], 0) | p in PROJECT];
# array[PROJECT, CONTRIBUTOR] of var bool: project_contributor;

# % ==== Roles =====================================================================

# array[ROLE] of par PROJECT: role_project;

# % Skill required for each role
# array[ROLE] of par SKILL: role_skill;

# % Minimum level required for each role
# array[ROLE] of par LEVEL: role_level;

# % Contributor assigned to each role
# array[ROLE] of var CONTRIBUTOR: role_contributor;

# % Mentor (optional) for each role
# array[ROLE] of var opt CONTRIBUTOR: role_mentor;

# % Did the contributor progress from this role?
# array[ROLE] of var bool: role_progress;

# % ==== Contributors ==============================================================

# array[CONTRIBUTOR, SKILL] of par LEVEL: contributor_skill;
# array[CONTRIBUTOR] of var set of ROLE: contributor_roles;

# % ==== Constraints ===============================================================

# function var LEVEL: get_level(var ROLE: r) =
#     let {
                        
#     var SKILL : s = role_skill[r];
#     var PROJECT: p = role_project[r];
#     var CONTRIBUTOR: c = role_contributor[r];
#     var LEVEL : base = contributor_skill[c, s];
                
#     var LEVEL : progress = 
#         sum (r2 in contributor_roles[c]) (                   
#             % Different role
#             (r != r2)
#             /\\
#             % Same skill
#             (role_skill[r2] = s)
#             /\\
#             % Project Before this
#             (project_end[role_project[r2]] <= project_start[p])
#             /\\
#             % Progressed from role
#             role_progress[r2]
#             )
#             ;
#     }
#     in
#     base + progress
# ;

# % Contributors satisfy the skill requirements for the roles
# constraint forall (r in ROLE) (
#     let {
#         par PROJECT : p    = role_project[r];
#         par SKILL   : s    = role_skill[r];
#         par LEVEL   : l    = role_level[r];
#         var CONTRIBUTOR: c = role_contributor[r];
#     }
#     in
#     % Contributor meets requirements
#     (
#         get_level(r) >= l
#         /\\
#         absent(role_mentor[r])
#     )
#     \\/
#     % Mentor exists
#     (
#         let {
#             var ROLE: r_m;
#             var CONTRIBUTOR: c_m = role_contributor[r_m];
#             var SKILL : s_m = role_skill[r_m];
#         }
#         in
#         r_m != r
#         /\\
#         c_m != c
#         /\\
#         s_m = s
#         /\\
#         get_level(r) = (l - 1)
#         /\\
#         get_level(r_m) >= l
#     )        
# )
# ;

# % Int Set Channel
# constraint int_set_channel(role_contributor, contributor_roles);

# % Contributors can only work on 1 role at a time
# constraint diffn(
#     [project_start[role_project[r]] | r in ROLE],
#     role_contributor,
#     [project_duration[role_project[r]] | r in ROLE],
#     [1 | r in ROLE]
# )
# ;

# solve maximize sum(project_score);
# """

#     max_skill = scenario.skills.count
#     max_proj  = scenario.projects.count
#     max_role  = scenario.roles.count
#     max_cont  = scenario.contributors.count
#     max_score = scenario.projects.map('best_score', int).max()
#     max_day   = scenario.projects.map('days', int).sum() + 1

#     project_duration   = [p.days for p in scenario.projects]
#     project_end_before = [p.end_before for p in scenario.projects]
#     project_best_score = [p.best_score for p in scenario.projects]

#     role_project = [r.proj_id for r in scenario.roles]
#     role_skill   = [r.skill_id for r in scenario.roles]
#     role_level   = [r.level for r in scenario.roles]
    
#     contributor_skill = [c.competencies.get(s, 0) for c in scenario.contributors for s in scenario.skills.keys]
    
#     async for result in solutions(
#         model_string,
#         options,
#         name = scenario.name,
#         max_skill=max_skill,
#         max_proj=max_proj,
#         max_role=max_role,
#         max_cont=max_cont,
#         max_score=max_score,
#         max_day=max_day,
#         project_duration=project_duration,
#         project_end_before=project_end_before,
#         project_best_score=project_best_score,
#         role_project=role_project,
#         role_skill=role_skill,
#         role_level=role_level,
#         contributor_skill=contributor_skill
#         ):
                        
#         if not result.status.has_solution:
#             log.error(f'"{result.name}" failed with status "{result.status}"')
#             continue

#         for contributor in scenario.contributors:
#             i = contributor.cont_id - 1
#             contributor.roles = Roles()
#             contributor.projects = Projects()
               
                
#         for project in scenario.projects:
#             i = project.proj_id - 1
                                    
#             project.staff = Contributors()
#             project.start = result['project_start', i]
#             project.end   = result['project_end', i]
#             project.score = result['project_score', i]
#             project.late  = result['project_late', i]
#             project.score = result['project_score', i]
                                                                                                            
#             for role in project.roles:
#                 i = role.role_id - 1

#                 role.start     = project.start
#                 role.end       = project.end
#                 role.contributor_id   = result['role_contributor',i]
#                 role.mentor_id = result['role_mentor',i] or 0
#                 role.mentor    = scenario.contributors.try_get(role.mentor_id)
#                 role.staff     = scenario.contributors[role.contributor_id]
                
#                 role.staff.roles += role
#                 role.staff.projects += project
#                 project.staff += role.staff


#         yield result


# from ortools.sat.python import cp_model


# def solve_with_ortools(scenario : Scenario):
#     yield True
#     return
            
#     model = cp_model.CpModel()
#     solver = cp_model.CpSolver()

#     num_skills = scenario.skills.count
#     num_projs  = scenario.projects.count
#     num_roles  = scenario.roles.count
#     num_staff  = scenario.contributors.count
#     max_score = scenario.projects.map('best_score', int).max()
#     max_day   = scenario.projects.map('days', int).sum() + 1
    
#     for p in scenario.projects:
#         p._start = model.NewIntVar(0, max_day, f'{p.name} Start')
#         p._end = model.NewIntVar(0, max_day, f'{p.name} End')
#         p._interval = model.NewIntervalVar(p._start, p.days, p._end, f'{p.name} Interval')
#         p._score = model.NewIntVar(0, max_score, f'{p.name} Score')
        
#     for r in scenario.roles:
#         r._staff = model.NewIntVar(1, num_staff, f'{r.project.name} {r.skill.name} Staff')

#     callback = SolutionCallback(scenario)
#     solver.Solve(model, callback)
    
#     log.debug(f'"{scenario.name}" - {solver.NumConflicts()} conflicts')
#     log.debug(f'"{scenario.name}" - {solver.NumBranches()} branches')
#     log.debug(f'"{scenario.name}" - {solver.NumBooleans()} booleans')
#     log.debug(f'"{scenario.name}" - {callback.iteration} Solutions')
#     log.debug(f'"{scenario.name}" - {solver.StatusName()}')

#     yield True



# class SolutionCallback(cp_model.CpSolverSolutionCallback):
#     def __init__(self, scenario : Scenario):
#         cp_model.CpSolverSolutionCallback.__init__(self)
#         self.scenario = scenario
#         self.iteration = 0

#     def on_solution_callback(self):
#         self.iteration += 1
#         log.debug(f'"{self.scenario.name}" iteration {self.iteration}')

#         for p in self.scenario.projects:
#             p.start = self.Value(p._start)        
#             p.end = self.Value(p._end)
        
#         for r in self.scenario.roles:
#             r.cont_id = self.Value(r._staff)
#             r.staff = self.scenario.contributors.get(r.cont_id)


# import altair as alt
# from altair import datum, Chart

# def get_records(scenario : Scenario):
#     for project in scenario.projects:
#         for role in project.roles:
#             skill = scenario.skills[role.skill_id]
#             staff = scenario.contributors.try_get(role.contributor_id)
            
#             record = dict(
#                 project = project.name,
#                 start_before = project.start_before,
#                 end_before = project.end_before,
#                 late = project.late,
#                 best_score = project.best_score,
#                 score = project.score,
#                 skill = skill.name,
#                 staff = staff.name if staff else '',
#                 role = f'{project.name} - {skill.name}',
#                 role_level = role.level,
#                 start = role.start,
#                 end = role.end,
#                 mid = (role.start + role.end) / 2.0, 
#                 days = project.days,
#             )
#             yield record
