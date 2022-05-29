#!/bin/bash

# Watch for changes in the source directory and rebuild
# the jupyter book
inotifywait \
    --quiet \
    --monitor \
    --event delete \
    --event close_write \
    --exclude __pycache__ \
    --exclude _build \
    book \
    | \
    while read dir event file; do \
        echo "${file} changed - building book" ; \
        jupyter-book build book ;\
    done
