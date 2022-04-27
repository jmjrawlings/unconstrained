#!/bin/bash
# Watch for changes in the Dagger CUE file and rerun 
# the debug task
inotifywait \
    --quiet \
    --monitor \
    --event delete \
    --event close_write \
    unconstrained.cue \
    | \
    while read dir event file; do \
        echo "${file} changed - running dagger" ; \
        dagger do Test --log-level debug --log-format plain ;\
    done
