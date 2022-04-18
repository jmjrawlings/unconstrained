package main

import (
  "dagger.io/dagger"
//   "dagger.io/dagger/core"
//   "universe.dagger.io/bash"
)

dagger.#Plan & {

    client: {
        filesystem:
            ".": read: contents: dagger.#FS
        commands:
            pytest: name: "pytest"
    }
    
    actions: {
        test: {
            result: client.commands.pytest.stdout            
        }
    }
}