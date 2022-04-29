# Unconstrained

Constraint Programming for Fun and Profit.

This repository represents my search for 
a comprehensive and productive environment to modelling and solving Constraint Programming problems.


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