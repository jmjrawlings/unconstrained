package main

import (
  "dagger.io/dagger"
  "dagger.io/dagger/core"
)

dagger.#Plan & {

    actions: {

        docker_build: 
            core.#Dockerfile & 
            {
            dockerfile: path: "Dockerfile"
            source: client.filesystem.".".read.contents
            target: "testing"
            }
        
        pytest: 
            core.#Exec & 
            {
            input: docker_build.output
            args: ["pytest"]
            }
        
        test_minizinc: 
            core.#Exec & 
            {
            input : docker_build.output
            args: ["minizinc", "--version"]
            always: true
            }

        test_python:
            core.#Exec & 
            {
            input : docker_build.output
            args: ["python3", "-m", "pytest"]
            always: true
            }

        debug:
        core.#Exec & 
            {
            input : docker_build.output
            args: ["which", "pytest"]
            always: true
            }

    }
    
    client: {

        filesystem: 
            ".": read: {
                contents: dagger.#FS
            }

        platform: {
            os: "linux"
            arch: "amd64"
        }

    }
}