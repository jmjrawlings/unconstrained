# Unconstrained

[![unconstrained](https://github.com/jmjrawlings/unconstrained/actions/workflows/test.yaml/badge.svg)](https://github.com/jmjrawlings/unconstrained/actions/workflows/test.yaml)

Constraint Programming for Fun and Profit.

This repository aims to provide a productive environment in which to to model and solve  Constraint Programming problems.


## Goals
- Model problems
- Compile models
- Solve models
- Evaluate solver performance
- Compare models
- Compare solver backends
- Visualise solutions/convergence
- Interactive frontend app
- Model persistence
- Development environment
- Python packages
- Python package management
- Logging
- Local and remote CI/CD
- Containerisation
- Cloud compute (maybe?)


## Non-Goals
- A production ready minizinc model builder
- A production ready anything
- A reusable python package
- A 'framework'
- Comprehensive documentation
- Backwards compatibility


## Principles
- Use Free open source tools
- Embrace development environments
- Embrace terminal
- Use python type hints liberally
- Hot-reload wherever possible
- Integration Tests


## Quickstart
- Install VSCode
- Install VSCode Remote Development Pack
- Open repo in VSCode
- Ctrl+Shift+P `Reopen Folder in Container`


## "The Stack"
The set of tools and packages I'm currently using to model and solve problems.  This will change over time.

### Visual Studio Code

#### Plugins

### MiniZinc

### Python

### Google ORTools

### Vega-Lite

### H20 Wave

### Docker

### Dagger


## Included Examples

| Name | Type | Model | Solve | Plot | .ipynb | App | Link |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| N-Queens | SAT | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :x: | :x: | [link](./examples/n_queens/README.md) |
| Nurse Rostering | OPT | :x: | :x: | :x: | :x: | :x: | [link](./examples/nurse_rostering/README.md) |
| Project Planning | OPT | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :x: | :x: | [link](./examples/project_planning/README.md) |


## Repository Structure
```
.
├── book                # Jupyter Book ouput
├── cue.mod             # Dagger dependencies
├── examples            # Example problems   
├── scripts             # Helper scripts
├── requirements        # Python requirement files
├── unconstrained       # Source code
├── tests               # Test suite
├── Dockerfile             
├── pytest.ini              
├── LICENSE.md              
├── README.md               
└── unconstrained.cue   # Dagger build file           
```


## Helpful Links

### Constraint Programming
- [MiniZinc](https://www.minizinc.org/)
- [MiniZinc Manual](https://www.minizinc.org/doc-latest/en/part_3_user_manual.html)
- [MiniZinc Reference](https://www.minizinc.org/doc-latest/en/part_4_reference.html)
- [MiniZinc Basic Modelling Course](https://www.coursera.org/learn/basic-modeling)
- [MiniZinc Advanced Modelling Course](https://www.coursera.org/learn/basic-modeling)
- [Discrete Algorithms Course](https://www.coursera.org/learn/solving-algorithms-discrete-optimization)
- [Google OR-Tools](https://developers.google.com/optimization)
- [Google OR-Tools GitHub](https://github.com/google/or-tools)
- [Google OR-Tools Manual](https://acrogenesis.com/or-tools/documentation/user_manual/)


### Python Packages
- [Altair](https://altair-viz.github.io/)
- [Pytest](https://docs.pytest.org/en/latest/)
- [Attrs](https://www.attrs.org/en/stable/)
- [Cattrs](https://cattrs.readthedocs.io/en/latest/)
- [SqlModel](https://github.com/tiangolo/sqlmodel)
- [Minizinc Python](https://github.com/MiniZinc/minizinc-python)


### Development Tools
- [Visual Studio Code](https://code.visualstudio.com/)
- [VSCode Devcontainer](https://code.visualstudio.com/docs/remote/containers)
- [Dagger](https://dagger.io/)
- [Dagger Docs](https://docs.dagger.io/)
- [CUE Lang](https://cuelang.org/)


## Notes

### Docker
- `apt-get` and `apt-install` takes forever which is very annoying when playing around with Dockerfiles.  Presumably theres a way to cache it but I can't quite figure it out.

### Devcontainer
- local variables (eg: {localEnv:USERNAME}) are not passed through properly from WSL2 to the container build

### Dagger
- Does dagger contain its own internal docker engine?
- Can we use the hosts docker engine by default to avoid repeat image builds?

### SqlModel
- Should normal functions be written with knowledge of the `session` ? Feels like the codebase would get polluted with a lot of sqlmodel code