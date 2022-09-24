#!/usr/bin/env bash

# Watch for changes in the Dagger CUE file and rerun
# the given action
dagger do $1 --log-level debug --log-format plain && \
inotifywait \
    --quiet \
    --monitor \
    --event delete \
    --event close_write \
    unconstrained.cue \
    | \
    while read dir event file; do \
        echo "${file} changed - running dagger action $1" ; \
        dagger do $1 --log-level debug --log-format plain ;\
    done
