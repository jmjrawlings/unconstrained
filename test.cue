package main

import (
  "dagger.io/dagger"
  "dagger.io/bash"
  "dagger.io/dagger/core"
)

#Echo: {
    msg: string | *"hello"
}

dagger.#Plan & {

    actions: 
        echo:
        #Echo & {
            msg: "xd"
        }

}
