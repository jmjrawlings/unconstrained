#!/bin/bash
inotifywait \
    --quiet \
    --monitor \
    --event delete \
    --event close_write \
    --exclude __pycache__ \
    --exclude _build \
    unconstrained/book \
    | \
    while read dir event file; do \
        echo "${file} changed - building book" ; \
        jupyter-book build unconstrained/book ;\
    done
