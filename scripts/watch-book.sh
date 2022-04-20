#!/bin/bash
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
