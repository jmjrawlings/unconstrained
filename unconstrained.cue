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
        #build_dockerfile_target: {
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
        #load_docker_image: cli.#Load & {
            host:  client.network."unix:///var/run/docker.sock".connect
        }

        // Build the testing docker image
        build_test_image: #build_dockerfile_target & {
            name: "test"
        }
                
        // Build the development docker image
        build_dev_image: #build_dockerfile_target & {
            name: "dev" 
        }

        // Build the production docker image
        build_prod_image: #build_dockerfile_target & {
            name: "prod" 
        }
                                                        
        // Load the test image into the hosts docker engine for debugging
        load_test_image: #load_docker_image & {
            image: build_test_image
            tag: "unconstrained:test"
        }

        // Load the dev image into the hosts docker engine for debugging
        load_dev_image: #load_docker_image & {
            image: build_dev_image
            tag: "unconstrained:dev"
        }

        // Run the test suite
        test: {

            // Run PyTest suite
            pytest: docker.#Run & {
                input: build_test_image
                }
        }
    }
}