#!/usr/bin/env bash

# Start pytest-watch with the given arguments
ptw --poll --runner "pytest $*"