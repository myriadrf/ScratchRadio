(function() {
    var ext = this;
    var fs = require('fs');
    var commandPipeName = "/tmp/lrcontrol/command.pipe";
    var commandPipe = null;

    // Send a command via the command pipe. Implements lazy open of
    // command pipe file.
    this._sendCommand = function(command) {
        if (commandPipe == null) {
            commandPipe = fs.openSync(commandPipeName, 'a');
        }
        fs.appendFileSync (commandPipe, command + "\n")
    }

    // Cleanup function when the extension is unloaded.
    ext._shutdown = function() {
        if (commandPipe != null) {
            fs.closeSync(commandPipe);
            commandPipe = null;
        }
    };

    // Status reporting code. Checks for the availability of the Lua Radio
    // control pipe. At the moment the LuaRadio driver script needs to be
    // started manually - it would be good to come up with a way of automating
    // this somehow.
    ext._getStatus = function() {
        if (!fs.existsSync(commandPipeName)) {
            return {status: 0, msg: 'No LuaRadio command pipe found'};
        }
        return {status: 2, msg: 'Ready'};
    };

    // Block for resetting the Lua Radio service.
    ext.radioReset = function() {
        this._sendCommand("RESET");
    }

    // Block for starting the Lua Radio service.
    ext.radioStart = function() {
        this._sendCommand("START");
    }

    // Block for stopping the Lua Radio service.
    ext.radioStop = function() {
        this._sendCommand("STOP");
    }

    // Block for creating a new SoapySDR radio source.
    ext.createRadioSource = function(name, frequency) {
        var scaledFreq = frequency * 1e6;
        this._sendCommand("CREATE RADIO-SOURCE " + name + " " + scaledFreq);
    };

    // Block for creating a new display plot sink.
    // TODO: Add configuration parameters.
    ext.createDisplaySink = function(name) {
        this._sendCommand("CREATE DISPLAY-SINK " + name);
    }

    // Block for creating a simple connection between a producer with a
    // single 'out' port and a consumer with a single 'in' port.
    ext.makeSimpleConnection = function(producer, consumer) {
        this._sendCommand("CONNECT " + producer + " out " + consumer + " in");
    }

    // Block and block menu descriptions
    var descriptor = {
        blocks: [
            // Block type, block name, function name
            [' ', 'reset radio', 'radioReset'],
            [' ', 'start radio', 'radioStart'],
            [' ', 'stop radio', 'radioStop'],
            [' ', 'create radio source %s at %n MHz', 'createRadioSource', 'lime-source', 868],
            [' ', 'create display sink %s', 'createDisplaySink', 'spectrum'],
            [' ', 'connect %s to %s', 'makeSimpleConnection', 'producer', 'consumer'],
        ]
    };

    // Register the extension
    ScratchExtensions.register('Lua Radio Extension', descriptor, ext);
})({});
