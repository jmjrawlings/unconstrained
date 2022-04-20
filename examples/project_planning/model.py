from unconstrained import *
from altair import Chart

input_dir  : Path  = to_existing_filepath(__file__).parent / 'input'
output_dir : Path = to_existing_filepath(__file__).parent / 'output'


@attr.s(**ATTRS)
class Skill(HasId):
    skill_id : int = int_field()
    name     : str = string_field()
                    
    def get_id(self):
        return self.skill_id


class Skills(Map[int, Skill]):
    key_type = int
    val_type = Skill


@attr.s(**ATTRS)
class Contributor(HasId):
    cont_id : int = int_field()
    name : str = string_field()
    competencies : Dict[int, int] = dict_field()

    """
    References
    """
    roles : "Roles" = None       # type:ignore
    projects : "Projects" = None # type:ignore
    
        
    def get_id(self):
        return self.cont_id


class Contributors(Map[int, Contributor]):
    key_type = int
    val_type = Contributor


@attr.s(**ATTRS)
class Role(HasId):
    """
    Input
    """
    role_id  : int = int_field()
    proj_id  : int = int_field()
    skill_id : int = int_field()
    level    : int = int_field()
    
    """
    Solution
    """
    cont_id   : int = int_field()
    mentor_id : int = int_field()
    start     : int = int_field()
    end       : int = int_field()
    days      : int = int_field()

    """
    References
    """
    project : "Project" = None # type:ignore
    skill   : Skill = None # type:ignore
    staff   : Optional[Contributor] = None
    mentor  : Optional[Contributor] = None
                    
    def get_id(self):
        return self.role_id


class Roles(Map[int, Role]):
    key_type = int
    val_type = Role
    

@attr.s
class Project(HasId):
    """
    Input
    """
    proj_id     : int   = int_field()
    name        : str   = string_field()
    days        : int   = int_field()
    best_score  : int   = int_field()
    end_before  : int   = int_field()
    start_before: int   = int_field()
    roles       : Roles = map_field(Roles)
    
    """
    Solution
    """
    start : int = int_field()
    end   : int = int_field()
    score : int = int_field()
    late  : int = int_field()

    """
    References
    """
    staff : Contributors = None # type:ignore
        
    
    def get_id(self):
        return self.proj_id


class Projects(Map[int, Project]):
    key_type = int
    val_type = Project


@attr.s(**ATTRS)
class Scenario(HasId):
    scen_id  : str      = string_field()
    name     : str      = string_field()
    skills   : Skills   = map_field(Skills)
    projects : Projects = map_field(Projects)
    roles    : Roles    = map_field(Roles)
    contributors : Contributors = map_field(Contributors)

    def get_id(self):
        return self.scen_id    

    def __str__(self):
        return f'"{self.name}" with {self.projects.count} projects and {self.contributors.count} contributors'

    def __repr__(self):
        return f'<{self!s}>'



def load_scenario(path) -> Scenario:

    path = to_existing_filepath(path)
    
    with path.open('r') as src:
                
        def line_tokens():
            return src.readline().split(' ')

        n_cont, n_proj = line_tokens()
        n_cont, n_proj = int(n_cont), int(n_proj)
        scen_id = path.stem.replace('.in','')[2:]
        name = scen_id.replace('_', ' ').title()
        
        scenario = Scenario(
            scen_id = scen_id,
            name = name,
        )
        
        skill_names = {}
                
        for _ in range(n_cont):
            name, n_skill = line_tokens()

            cont = Contributor(
                cont_id = scenario.contributors.count + 1,
                name = name
            )
            scenario.contributors += cont
            comp_id=0
                                                
            for _ in range(int(n_skill)):
                comp_id += 1
                skill_name, level = line_tokens()

                skill = skill_names.get(skill_name)
                
                if not skill:
                    skill = Skill(
                        skill_id = len(skill_names) + 1,
                        name = skill_name
                        )
                    scenario.skills += skill
                    skill_names[skill_name] = skill

                cont.competencies[skill.skill_id] = int(level)
                

        for _ in range(n_proj):
            line = line_tokens()
            name, days, best_score, best_before, n_roles = line
            days = int(days)
            best_score = int(best_score)
            best_before = int(best_before)
            n_roles = int(n_roles)
                                                            
            project = Project(
                proj_id = scenario.projects.count + 1,
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
                    role_id = scenario.roles.count + 1,
                    proj_id = project.proj_id,
                    skill_id = skill.skill_id,
                    level = level
                )
                role.skill = skill
                role.project = project
                project.roles += role
                scenario.roles += role

            scenario.projects += project                

    log.info(f'loaded "{scenario!r}" from "{path}"')
    return scenario