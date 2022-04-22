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
            }

        test_python:
            core.#Exec & 
            {
            input : docker_build.output
            args: ["which", "python"]
            }

    }
    
    client: {

        filesystem: 
            ".": read: {
                contents: dagger.#FS
            }
                

    }
}