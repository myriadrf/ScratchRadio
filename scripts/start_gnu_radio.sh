#!/bin/bash
#
# Starts the GNU Radio driver script which is used by Scratch to access the
# GNU Radio functionality. Currently runs the script in the foreground for
# tracing activity on the console.
#
GR_SCRIPT_NAME="/usr/lib/scratch2/scratch_extensions/gnuRadioDriver.py"
COMMAND_PIPE_DIR="/tmp/gr-control"
COMMAND_PIPE_NAME=$COMMAND_PIPE_DIR/"command.pipe"
TX_MSG_PIPE_NAME=$COMMAND_PIPE_DIR/"txmessage.pipe"
RX_MSG_PIPE_NAME=$COMMAND_PIPE_DIR/"rxmessage.pipe"
SCRIPT_LOCK_NAME=$COMMAND_PIPE_DIR/"script.lock"

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

# Runs the GNU Radio script. Uses flock to ensure only one instance is running.
flock -w 0.1 $SCRIPT_LOCK_NAME python $GR_SCRIPT_NAME
