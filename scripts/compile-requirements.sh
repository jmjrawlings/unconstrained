#!/usr/bin/env bash

set -eo pipefail

SCRIPT="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REQ=$(dirname "$SCRIPT")/requirements

function compile() {
    env="$1"
    start_time=$SECONDS
    echo -n "Compiling $env requirements ... "
    input_file="$REQ/requirements-$env.in"
    output_file="$REQ/requirements-$env.txt"
    pip-compile \
        --resolver=backtracking  \
        --output-file "$output_file" \
        --strip-extras \
        $input_file

    end_time=$SECONDS
    count=$(grep -c "^[a-Z]" ${output_file})
    elapsed="$(( end_time - start_time ))"    
    echo "$Compiled $count $env packages in ${elapsed}s"
}

function sync() {
    start_time=$SECONDS
    echo "Syncing dev environment ... "
    pip-sync "$REQ/requirements-dev.txt"
    end_time=$SECONDS
    elapsed="$(( end_time - start_time ))"
    echo "Syncing dev environment took ${elapsed}s"
}

for env in prod test dev
do compile $env
done

sync
