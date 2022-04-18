package main

import (
  "dagger.io/dagger"
  "dagger.io/dagger/core"
)

dagger.#Plan & {

    client:
        filesystem:
        ".": 
            read: {
                contents: dagger.#FS
            }

    actions:
        test: core.#Exec & {
            args: ["echo", "xd"]
            user: ""
            input: client.filesystem.".".read.contents
    }
}