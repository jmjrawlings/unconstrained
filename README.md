# Unconstrained

[![unconstrained](https://github.com/jmjrawlings/unconstrained/actions/workflows/test.yaml/badge.svg)](https://github.com/jmjrawlings/unconstrained/actions/workflows/test.yaml)

My personal development environment for modelling and solving constraint programming problems in python.

## Features
- A fully featured [devcontainer](https://code.visualstudio.com/docs/devcontainers/containers) 
    - Python
    - MiniZinc
    - Google ORTools
- A test dockerfile target (no dev dependencies)
- A prod dockerfile target (no test dependencies)
- Some example models (need more)
    - [N-Queens](./models/queens/)
    - [Nurse Rostering](./models/rostering)
- [A strongly typed wrapper for minizinc model results](./unconstrained/minizinc/minizinc.py)
- [A strongly typed Map class (dict replacement)](./unconstrained/prelude/map.py)
- [A strongly typed List class (list replacement)](./unconstrained/prelude/list.py)
- [Convenience functions for defining attrs models](./unconstrained/model/mode.py)
- [CI/CD scripts using dagger-io](./build/build.py)
    - Deployed to [Github](./.github/workflows/test.yaml)
- [Multi layered python package dependency management using pip-tools](./requirements/)


## Repository Structure
```
.
├── examples       # Example problems   
├── scripts        # Helper scripts
├── requirements   # Python requirement files
├── build          # Build scripts
├── unconstrained  # Source code
├── tests          # Test suite
├── Dockerfile             
├── pytest.ini              
├── LICENSE.md              
└── README.md               
```


## Links

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
- [Attrs](https://www.attrs.org/en/stable/)
- [Cattrs](https://catt.rs/en/stable/)
- [OR-Tools](https://developers.google.com/optimization)
- [Minizinc](https://github.com/MiniZinc/minizinc-python)
- [Pytest](https://docs.pytest.org/en/latest/)


### Development Tools
- [Visual Studio Code](https://code.visualstudio.com/)
- [VSCode Devcontainer](https://code.visualstudio.com/docs/remote/containers)
- [Dagger](https://dagger.io/)


## Notes / TODO

### Docker
- `apt-get` and `apt-install` takes forever which is very annoying when playing around with Dockerfiles.  Presumably theres a way to cache it but I can't quite figure it out.

### Devcontainer
- local variables (eg: {localEnv:USERNAME}) are not passed through properly from WSL2 to the container build

### Dagger
- Does dagger contain its own internal docker engine?
- Can we use the hosts docker engine by default to avoid repeat image builds?