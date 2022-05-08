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

        // Build a target image from the main Dockerfile
        #_dockerfileTarget: {
            name: string
            _build: core.#Dockerfile & 
                {
                dockerfile: path: "Dockerfile"
                target: name
                source: client.filesystem.".".read.contents
                }
            
            rootfs: _build.output
            config: _build.config
        }
        
        // Load a docker image into the hosts docker engine
        #_loadDockerImage: cli.#Load & {
            host:  client.network."unix:///var/run/docker.sock".connect
        }

        // Test Image
        _testImage: #_dockerfileTarget & {
            name: "test"
        }
                
        // Dev Image
        _devImage: #_dockerfileTarget & {
            name: "dev" 
        }
                
        // Load the Test image into the hosts docker engine
        LoadTest: #_loadDockerImage & {
            image: _testImage
            tag: "unconstrained:test"
        }

        // Load the Dev image into the hosts docker engine
        LoadDev: #_loadDockerImage & {
            image: _devImage
            tag: "unconstrained:dev"
        }

        // Run the test suite
        Test: {
            
            // Test Python is installed
            PythonInstalled: docker.#Run & 
                {
                input : _testImage
                command: {
                    name: "python3"
                    args: ["--version"]
                }
            }

            // Test MiniZinc is installed
            MiniZincInstalled: docker.#Run & 
                {
                input : _testImage
                command: {
                    name: "minizinc"
                    args: ["--version"]
                }
                }

            // Run PyTest suite
            PyTest: docker.#Run & 
                {
                input: _testImage
                command: {
                    name: "pytest"
                }
            }
        }
    }

}