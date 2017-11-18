#!/bin/bash
#
# Starts the Lua Radio driver script which is used by Scratch to access the
# Lua Radio functionality. Currently runs the script in the foreground for
# tracing activity on the console.
#
LUA_SCRIPT_NAME="/usr/lib/scratch2/scratch_extensions/luaRadioDriver.lua"
COMMAND_PIPE_DIR="/tmp/lrcontrol"
COMMAND_PIPE_NAME=$COMMAND_PIPE_DIR/"command.pipe"
TX_MSG_PIPE_NAME=$COMMAND_PIPE_DIR/"txmessage.pipe"
RX_MSG_PIPE_NAME=$COMMAND_PIPE_DIR/"rxmessage.pipe"

# Ensure the command pipe directory is present.
mkdir -p $COMMAND_PIPE_DIR

# Creates the named pipes if not already present.
if ! [ -p $COMMAND_PIPE_NAME ]
then
    rm -f $COMMAND_PIPE_NAME
    mkfifo $COMMAND_PIPE_NAME
fi

if ! [ -p $TX_MSG_PIPE_NAME ]
then
    rm -f $TX_MSG_PIPE_NAME
    mkfifo $TX_MSG_PIPE_NAME
fi

if ! [ -p $RX_MSG_PIPE_NAME ]
then
    rm -f $RX_MSG_PIPE_NAME
    mkfifo $RX_MSG_PIPE_NAME
fi

# Runs the Lua Radio script.
LUARADIO_DEBUG=1 luaradio $LUA_SCRIPT_NAME $COMMAND_PIPE_NAME
