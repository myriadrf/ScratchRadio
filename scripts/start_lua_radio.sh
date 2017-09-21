#!/bin/bash
#
# Starts the Lua Radio driver script which is used by Scratch to access the
# Lua Radio functionality. Currently runs the script in the foreground for
# tracing activity on the console.
#
LUA_SCRIPT_NAME="/usr/lib/scratch2/scratch_extensions/luaRadioDriver.lua"
COMMAND_PIPE_DIR="/tmp/lrcontrol"
COMMAND_PIPE_NAME=$COMMAND_PIPE_DIR/"command.pipe"

# Creates the named pipe if not already present.
if ! [ -p $COMMAND_PIPE_NAME ]
then
    rm -f $COMMAND_PIPE_NAME
    mkdir -p $COMMAND_PIPE_DIR
    mkfifo $COMMAND_PIPE_NAME
fi

# Runs the Lua Radio script.
luajit -- $LUA_SCRIPT_NAME $COMMAND_PIPE_NAME
