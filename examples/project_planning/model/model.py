from unconstrained import *

class Paths:
    """ Filepaths """
    
    home = Path(__file__).parent
    input = home / 'input'
    output = home / 'output'
    database = output / 'project_planning.db'


Model = db.create_model_class()


class Scenario(Model, table=True):
    name : str = db.column()

    # Relationships
    skills : List["Skill"] = db.relation('scenario')
    projects : List["Project"] = db.relation('scenario')
    contributors : List["Contributor"] = db.relation('scenario')


class Skill(Model, table=True):
    name : str = db.column()
    scenario_id : int = db.foreign_key(Scenario.id)
    scenario : "Scenario" = db.relation('skills')

    competencies : List["Competency"] = db.relation('skill')
    roles : List["Role"] = db.relation('skill')
            

class Contributor(Model, table=True):
    name : str = db.column()
    scenario_id : int = db.foreign_key(Scenario.id)
    scenario : "Scenario" = db.relation('contributors')

    competencies : List["Competency"] = db.relation('contributor')


class Competency(Model, table=True):
    skill_id : int = db.foreign_key(Skill.id)
    contributor_id : int = db.foreign_key(Contributor.id)
    level : int = db.column()

    skill : Skill = db.relation(Skill.competencies)
    contributor : Contributor = db.relation(Contributor.competencies)


class Role(Model, table=True):
    skill_id : int = db.foreign_key(Skill.id, default=None)
    project_id : int = db.foreign_key('project.id', default=None)
    contributor_id : Optional[int] = db.foreign_key(Contributor.id, default=None)
    mentor_id : Optional[int] = db.foreign_key(Contributor.id, default=None)
    level : int = db.column()
    start : Optional[int] = db.column(default=None)
    end : Optional[int] = db.column(default=None)
    days : Optional[int] = db.column(default=None)

    skill : Skill = db.relation('roles')
    project : "Project" = db.relation("roles")
       

class Project(Model, table=True):
    scenario_id : int     = db.foreign_key(Scenario.id)
    name        : str     = db.column()
    days        : int     = db.column()
    best_score  : int     = db.column()
    end_before  : int     = db.column()
    start_before: int     = db.column()
    start : Optional[int] = db.column(default=None)
    end   : Optional[int] = db.column(default=None)
    score : Optional[int] = db.column(default=None)
    late  : Optional[int] = db.column(default=None)

    scenario : "Scenario" = db.relation(Scenario.projects)
    roles : List[Role] = db.relation('project')

    

def create_scenario(path : Path) -> Scenario:
        
    path = to_existing_filepath(path)
    
    with path.open('r') as src:
                
        def line_tokens():
            return src.readline().split(' ')

        n_cont, n_proj = line_tokens()
        n_cont, n_proj = int(n_cont), int(n_proj)
        scen_id = path.stem.replace('.in','')[2:]
        name = scen_id.replace('_', ' ').title()
        
        scenario = Scenario(
            name = name,
        )
        
        skill_names = {}
                
        for _ in range(n_cont):
            name, n_skill = line_tokens()

            contributor = Contributor(
                name = name
            )
            comp_id=0
                                                
            for _ in range(int(n_skill)):
                comp_id += 1
                skill_name, level = line_tokens()

                skill = skill_names.get(skill_name)
                
                if not skill:
                    skill = Skill(
                        name = skill_name
                        )
                    scenario.skills.append(skill)
                    skill_names[skill_name] = skill

                competency = Competency(contributor=contributor, skill=skill, level=int(level))
                contributor.competencies.append(competency)

        for _ in range(n_proj):
            line = line_tokens()
            name, days, best_score, best_before, n_roles = line
            days = int(days)
            best_score = int(best_score)
            best_before = int(best_before)
            n_roles = int(n_roles)
                                                            
            project = Project(
                scenario=scenario,
                name = name,
                days = days,
                best_score = best_score,
                start_before = best_before - days,
                end_before = best_before,
            )
                        
            for _ in range(int(n_roles)):
                skill_name, level = line_tokens()
                skill = skill_names[skill_name]
                role = Role(
                    project=project,
                    skill=skill,
                    level = int(level)
                )

    log.info(f'loaded "{scenario!r}" from "{path.name}"')
    return scenario
