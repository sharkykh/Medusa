#!/bin/bash
set -e

if [[ -z $CIRCLE_PULL_REQUEST ]]; then
    echo "This is not a pull-request, skipping"
    exit 0
fi

# This script expects to be run in: Medusa/themes-default/slim
path_to_built_themes="../../themes/"

# Helper function to print the command before running it.
run_verbose () {
    echo "\$ $*"
    eval $*
}

get_size () {
    du -sb $1 | cut -f1
}

# We need to get the PR's base/target branch, since CircleCI doesn't provide it
merge_base_commit=$(git merge-base origin/develop origin/master $CIRCLE_BRANCH | tr -d ' ')
if [[ -z $merge_base_commit ]]; then
    echo "merge_base_commit is empty!"
    exit 1
fi

target_branch=$(git branch --points-at=$merge_base_commit | tr -d ' ')
if [[ -z $target_branch ]]; then
    echo "Target branch is empty!"
    exit 1
fi

echo "Target branch: $target_branch"
run_verbose "git merge $target_branch --no-commit"

# Determine if and how to build the Webpack bundle.
build_cmd=""
build_mode=""

# Do not build on other branches because it will cause conflicts on pull requests,
#   where push builds build for development and PR builds build for production.
if [[ $target_branch == "master" ]]; then
    build_cmd="yarn build"
    build_mode="production"
elif [[ $target_branch == "develop" ]]; then
    build_cmd="yarn dev"
    build_mode="development"
fi

# Keep track of the current themes size.
size_before=$(get_size $path_to_built_themes)

# Build themes.
[[ -n $build_cmd ]] && run_verbose "$build_cmd"
run_verbose "yarn gulp sync"

# Keep track of the new themes size.
size_after=$(get_size $path_to_built_themes)

echo "Themes size before: $size_before"
echo "Themes size after: $size_after"

# Check if the themes changed.
status="$(git status --porcelain -- $path_to_built_themes)";
if [[ -n $status && $size_before != $size_after ]]; then
    if [[ -z $build_mode ]]; then
        echo "Please build the themes"
        echo "-----------------------"
    else
        echo "Please build the themes (mode: $build_mode) "
        echo "--------------------------------------------"
    fi
    echo "$status"
    exit 1
fi
