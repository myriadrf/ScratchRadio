(function() {
    var ext = this;
    var C = require('constants')
    var fs = require('fs');
    var commandPipeName = "/tmp/lrcontrol/command.pipe";
    var txMsgPipeName = "/tmp/lrcontrol/txmessage.pipe";
    var rxMsgPipeName = "/tmp/lrcontrol/rxmessage.pipe";
    var commandPipe = null;
    var txMsgPipe = null;
    var rxMsgPipe = null;
    var txMsgStart = false;
    var rxMsgStart = false;
    var radioRunning = false;
    var rxMsgBufSize = 255;
    var rxMsgBuffer = Buffer.alloc(rxMsgBufSize);
    var rxMsgOffset = 0;
    
    // Send a command via the command pipe. Implements lazy open of
    // command pipe file.
    this._sendCommand = function(command) {
        if (commandPipe == null) {
            commandPipe = fs.openSync(commandPipeName, 'a');
        }
        fs.appendFileSync (commandPipe, command + "\n");
    }

    // Send a message via the transmit message pipe.
    this._sendMessage = function(message) {
        if (txMsgPipe != null) {
            fs.appendFileSync (txMsgPipe, message + "\n");
        }
    }
    
    // Receive a message via the response message pipe.
    this._receiveMessage = function(callback) {
    	if (rxMsgPipe == null) {
            callback("Broken Rx Message Pipe");
        } else {
            fs.read(rxMsgPipe, rxMsgBuffer, rxMsgOffset, rxMsgBufSize-rxMsgOffset, null,
                function(err, len, buf) {
                    if (err == null) {
                        if (len == 0) {
                            this._receiveMessage(callback)
                        } else {
                            var rxMsgString;
                            rxMsgOffset += len;
                            for (var i = 0; i < rxMsgOffset; i++) {
                            
                                // On detecting an end of line character, copy
                                // the line to the received message string and
                                // shift the residual buffer contents down.
                                if (buf[i] == 10) {
                                    rxMsgString = buf.toString('ascii', 0, i);
                                    if (i == rxMsgOffset-1) {
                                        rxMsgOffset = 0;	    
                                    } else {
                                        buf.copy(buf, 0, i+1, rxMsgOffset-i-1);
                                        rxMsgOffset -= i+1;
                                    }
                                    break;
                                }
                            }
                               
                            // Invoke callback or retry.
                            if (rxMsgString == null) {
                                if (rxMsgOffset >= rxMsgBufSize) {
                                    rxMsgOffset -= 1;
                                } 
                                this._receiveMessage(callback)
                            } else { 
                                callback(rxMsgString);
                            } 
                        }
                    } else if (err.code == "EAGAIN") {
                        this._receiveMessage(callback)
                    } else {
                        callback("Rx Message Error : " + err.code)
                    }
                }
            );
        }
    }

    // Cleanup function when the extension is unloaded.
    ext._shutdown = function() {
        if (commandPipe != null) {
            fs.closeSync(commandPipe);
            commandPipe = null;
        }
        if (txMsgPipe != null) {
            fs.closeSync(txMsgPipe);
            txMsgPipe = null;
        }	
        if (rxMsgPipe != null) {
            fs.closeSync(rxMsgPipe);
            rxMsgPipe = null;
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
        if (!fs.existsSync(txMsgPipeName)) {
            return {status: 0, msg: 'No LuaRadio transmit pipe found'};
        }
        if (!fs.existsSync(rxMsgPipeName)) {
            return {status: 0, msg: 'No LuaRadio receive pipe found'};
        }
        return {status: 2, msg: 'Ready'};
    };

    // Block for resetting the Lua Radio service.
    ext.radioReset = function() {
    	if (radioRunning) {
    	    this.radioStop()	
    	}
    	txMsgStart = false;
    	rxMsgStart = false;
        this._sendCommand("RESET");
    }

    // Block for starting the Lua Radio service.
    ext.radioStart = function() {
        this._sendCommand("START");
        if (txMsgStart && (txMsgPipe == null)) {
            txMsgPipe = fs.openSync(txMsgPipeName, 'a');
        }
        if (rxMsgStart && (rxMsgPipe == null)) {
            rxMsgPipe = fs.openSync(rxMsgPipeName, C.O_NONBLOCK);
        }
    	radioRunning = true;
    }
    
    // Block for stopping the Lua Radio service.
    ext.radioStop = function() {
        this._sendCommand("STOP");
    	radioRunning = false;
        if (txMsgPipe != null) {
            fs.closeSync(txMsgPipe);
            txMsgPipe = null;
        }	
        if (rxMsgPipe != null) {
            fs.closeSync(rxMsgPipe);
            rxMsgPipe = null;
        }	
    }

    // Determine if the radio has been started.
    ext.isRadioRunning = function() {
        return radioRunning;	    
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

    // Block for creating a transmit message source.
    ext.createMessageSource = function(name) {
    	txMsgStart = true;
        this._sendCommand("CREATE MESSAGE-SOURCE " + name + " " + txMsgPipeName);
    }

    // Block for creating a receive message sink.
    ext.createMessageSink = function(name) {
    	rxMsgStart = true;
        this._sendCommand("CREATE MESSAGE-SINK " + name + " " + rxMsgPipeName);
    }

    // Block for creating a simple transmit framer.
    ext.createSimpleFramer = function(name) {
        this._sendCommand("CREATE SIMPLE-FRAMER " + name);
    }

    // Block for creating a simple receive deframer.
    ext.createSimpleDeframer = function(name) {
        this._sendCommand("CREATE SIMPLE-DEFRAMER " + name);
    }

    // Block for creating a Manchester encoder.
    ext.createManchesterEncoder = function(name) {
        this._sendCommand("CREATE MANCHESTER-ENCODER " + name);
    }

    // Block for creating a simple receive deframer.
    ext.createManchesterDecoder = function(name) {
        this._sendCommand("CREATE MANCHESTER-DECODER " + name);
    }
    
    // Block for creating a simple connection between a producer with a
    // single 'out' port and a consumer with a single 'in' port.
    ext.makeSimpleConnection = function(producer, consumer) {
        this._sendCommand("CONNECT " + producer + " out " + consumer + " in");
    }
    
    // Send a fixed message over the radio.
    ext.sendSimpleMessage = function(message) {
        this._sendMessage(message);
    }

    // Receive a message over the radio.
    ext.receiveSimpleMessage = function(callback) {
        this._receiveMessage(callback);
    }
    
    // Block and block menu descriptions
    var descriptor = {
        blocks: [
            // Block type, block name, function name
            [' ', 'reset radio', 'radioReset'],
            [' ', 'start radio', 'radioStart'],
            [' ', 'stop radio', 'radioStop'],
            ['b', 'radio running', 'isRadioRunning'],
            [' ', 'create radio source %s at %n MHz', 'createRadioSource', 'lime-source', 868],
            [' ', 'create display sink %s', 'createDisplaySink', 'spectrum'],
            [' ', 'create message source %s', 'createMessageSource', 'tx-message'],
            [' ', 'create message sink %s', 'createMessageSink', 'rx-message'],
            [' ', 'create simple framer %s', 'createSimpleFramer', 'tx-framer'],
            [' ', 'create simple deframer %s', 'createSimpleDeframer', 'rx-deframer'],
            [' ', 'create Manchester encoder %s', 'createManchesterEncoder', 'mcr-encoder'],
            [' ', 'create Manchester decoder %s', 'createManchesterDecoder', 'mcr-decoder'],
            [' ', 'connect %s to %s', 'makeSimpleConnection', 'producer', 'consumer'],
            [' ', 'send message %s', 'sendSimpleMessage', 'Hello World'],
            ['R', 'receive message', 'receiveSimpleMessage'],
        ]
    };

    // Register the extension
    ScratchExtensions.register('Lua Radio Extension', descriptor, ext);
})({});
