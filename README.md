# Unconstrained

[![unconstrained](https://github.com/jmjrawlings/unconstrained/actions/workflows/test.yaml/badge.svg)](https://github.com/jmjrawlings/unconstrained/actions/workflows/test.yaml)

My personal python development environment for solving constraint programming problems.

## Features
- MiniZinc + Google ORTools integration
- Prod/Test/Dev docker containers
- VSCode devcontainer integration
- A couple of example problems


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
- [Pydantic](https://docs.pydantic.dev/latest/)sqlmodel)
- [Minizinc](https://github.com/MiniZinc/minizinc-python)
- [Pytest](https://docs.pytest.org/en/latest/)


### Development Tools
- [Visual Studio Code](https://code.visualstudio.com/)
- [VSCode Devcontainer](https://code.visualstudio.com/docs/remote/containers)
- [Dagger](https://dagger.io/)


## Notes

### Docker
- `apt-get` and `apt-install` takes forever which is very annoying when playing around with Dockerfiles.  Presumably theres a way to cache it but I can't quite figure it out.

### Devcontainer
- local variables (eg: {localEnv:USERNAME}) are not passed through properly from WSL2 to the container build

### Dagger
- Does dagger contain its own internal docker engine?
- Can we use the hosts docker engine by default to avoid repeat image builds?
