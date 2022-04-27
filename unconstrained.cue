package main

import (
  "dagger.io/dagger"
  "dagger.io/dagger/core"
  "universe.dagger.io/docker/cli"
  "universe.dagger.io/docker"
)

dagger.#Plan & {
    
    client: {

        // Allow read access to the host filesystem
        filesystem: 
            ".": 
                read: contents: dagger.#FS

        // Allow access to the host docker runtime
        network:
            "unix:///var/run/docker.sock":
                connect: dagger.#Socket

    }
    
    actions: {
                
        BuildTestingImage: core.#Dockerfile & 
            {
            dockerfile: path: "Dockerfile"
            source: client.filesystem.".".read.contents
            target: "testing"
            }

        TestingImage: {
            rootfs: BuildTestingImage.output
            config: BuildTestingImage.config
        }
        
        LoadTestingImage: cli.#Load & 
            {
            image: TestingImage
            host:  client.network."unix:///var/run/docker.sock".connect
            tag:   "unconstrained:testing"
            }

        BuildDevelopmentImage: core.#Dockerfile & 
            {
            dockerfile: path: "Dockerfile"
            source: client.filesystem.".".read.contents
            target: "development"
            }

        DevelopmentImage: {
            rootfs: BuildDevelopmentImage.output
            config: BuildDevelopmentImage.config
        }
                
        LoadDevelopmentImage: cli.#Load & 
            {
            image: DevelopmentImage            
            host:  client.network."unix:///var/run/docker.sock".connect
            tag:   "unconstrained:development"
            }

        PyTest: docker.#Run & 
            {
            always: true
            input: TestingImage
            command: {
                name: "pytest"
            }
            }
        
        TestMiniZincInstalled: docker.#Run & 
            {
            input : TestingImage
            command: {
                name: "minizinc"
                args: ["--version"]
            }
            }

        TestPythonInstalled: docker.#Run & 
            {
            input : TestingImage
            command: {
                name: "python3"
                args: ["--version"]
            }
            }

        Test: {
            pytest: PyTest
            minizinc: TestMiniZincInstalled
            python: TestPythonInstalled
        }
    }

}