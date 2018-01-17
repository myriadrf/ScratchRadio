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
    var messageBitRate = 1600;
    var sampleRate = 499200;
    var errorCallbacks = [];
    var componentNameSet = new Set();
    var componentNameHook = null;

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

    // Issues an error message to any error listeners.
    this._errorMessage = function(message) {
        while (errorCallbacks.length > 0) {
            var callback = errorCallbacks.pop();
            callback(message);
        }
    }

    // Checks for duplicate component names.
    this._checkComponentAbsent = function(componentName) {
        if (componentNameSet.has(componentName)) {
            this._errorMessage("Duplicate component name : " + componentName);
            return false;
        } else {
            componentNameSet.add(componentName);
            return true;
        }
    }

    // Check for existing component names.
    this._checkComponentPresent = function(componentName) {
        if (!componentNameSet.has(componentName)) {
            this._errorMessage("Component not found : " + componentName);
            return false;
        } else {
            return true;
        }
    }

    // Implicitly connects up a data source.
    this._connectDataSource = function(componentName) {
        if (componentNameHook != null) {
            this._errorMessage("Source component should not have an input : " + componentName);
            return false;
        } else {
            componentNameHook = componentName;
            return true;
        }
    }

    // Implicitly connects up a data sink.
    this._connectDataSink = function(componentName) {
        if (componentNameHook == null) {
            this._errorMessage("Sink component must have an input : " + componentName);
            return false;
        } else {
            this._sendCommand("CONNECT " + componentNameHook + " out " + componentName + " in");
            componentNameHook = null;
            return true;
        }
    }

    // Implicitly connects up a data processing component.
    this._connectDataProcessor = function(componentName) {
        if (componentNameHook == null) {
            this._errorMessage("Data processing component must have an input : " + componentName);
            return false;
        } else {
            this._sendCommand("CONNECT " + componentNameHook + " out " + componentName + " in");
            componentNameHook = componentName;
            return true;
        }
    }

    // Receive a message via the response message pipe.
    this._receiveMessage = function(callback) {
        if (rxMsgPipe == null) {
            this._errorMessage("Radio Not Running");
            callback("");
        } else {
            fs.read(rxMsgPipe, rxMsgBuffer, rxMsgOffset, rxMsgBufSize-rxMsgOffset, null,
                function(err, len, buf) {
                    if (err == null) {
                        if (len == 0) {
                            this._receiveMessage(callback);
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
                                this._receiveMessage(callback);
                            } else {
                                callback(rxMsgString);
                            }
                        }
                    } else if (err.code == "EAGAIN") {
                        this._receiveMessage(callback);
                    } else {
                        this._errorMessage("Rx Message Error : " + err.code);
                        callback("");
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
        componentNameSet.clear();
        componentNameHook = null;
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
        if (this._checkComponentAbsent(name)) {
            var scaledFreq = frequency * 1e6;
            this._sendCommand("CREATE RADIO-SOURCE " + name + " " + scaledFreq + " " + sampleRate);
            this._connectDataSource(name);
        }
    };

    // Block for creating a new SoapySDR radio sink.
    ext.createRadioSink = function(name, frequency) {
        if (this._checkComponentAbsent(name)) {
            var scaledFreq = frequency * 1e6;
            this._sendCommand("CREATE RADIO-SINK " + name + " " + scaledFreq + " " + sampleRate);
            this._connectDataSink(name);
        }
    };

    // Block for creating a new display plot sink.
    // TODO: Add configuration parameters.
    ext.createDisplaySink = function(name) {
        if (this._checkComponentAbsent(name)) {
            this._sendCommand("CREATE DISPLAY-SINK " + name);
            this._connectDataSink(name);
        }
    }

    // Block for creating a transmit message source.
    ext.createMessageSource = function(name) {
        if (this._checkComponentAbsent(name)) {
            txMsgStart = true;
            this._sendCommand("CREATE MESSAGE-SOURCE " + name +
                " " + txMsgPipeName + " " + (messageBitRate / 8));
            this._connectDataSource(name);
        }
    }

    // Block for creating a receive message sink.
    ext.createMessageSink = function(name) {
        if (this._checkComponentAbsent(name)) {
            rxMsgStart = true;
            this._sendCommand("CREATE MESSAGE-SINK " + name + " " + rxMsgPipeName);
            this._connectDataSink(name);
        }
    }

    // Block for creating a simple transmit framer.
    ext.createSimpleFramer = function(name) {
        if (this._checkComponentAbsent(name)) {
            this._sendCommand("CREATE SIMPLE-FRAMER " + name);
            this._connectDataProcessor(name);
        }
    }

    // Block for creating a simple receive deframer.
    ext.createSimpleDeframer = function(name) {
        if (this._checkComponentAbsent(name)) {
            this._sendCommand("CREATE SIMPLE-DEFRAMER " + name);
            this._connectDataProcessor(name);
        }
    }

    // Block for creating a Manchester encoder.
    ext.createManchesterEncoder = function(name) {
        if (this._checkComponentAbsent(name)) {
            this._sendCommand("CREATE MANCHESTER-ENCODER " + name);
            this._connectDataProcessor(name);
        }
    }

    // Block for creating a simple receive deframer.
    ext.createManchesterDecoder = function(name) {
        if (this._checkComponentAbsent(name)) {
            this._sendCommand("CREATE MANCHESTER-DECODER " + name);
            this._connectDataProcessor(name);
        }
    }

    // Block for creating an OOK modulator.
    ext.createOokModulator = function(name, intFreq) {
        if (this._checkComponentAbsent(name)) {
            this._sendCommand("CREATE OOK-MODULATOR " + name + " " +
                Math.round(sampleRate / (2 * messageBitRate)) + " " +
                ((intFreq * 1000) / (2 * messageBitRate)));
            this._connectDataProcessor(name);
        }
    }

    // Block for creating an OOK demodulator.
    ext.createOokDemodulator = function(name) {
        if (this._checkComponentAbsent(name)) {
            this._sendCommand("CREATE OOK-DEMODULATOR " + name + " " + (messageBitRate * 2));
            this._connectDataProcessor(name);
        }
    }

    // Block for creating a bit rate sampler.
    ext.createBitRateSampler = function(name) {
        if (this._checkComponentAbsent(name)) {
            this._sendCommand("CREATE BIT-RATE-SAMPLER " + name + " " + (messageBitRate * 2));
            this._connectDataProcessor(name);
        }
    }

    // Block for creating the real valued file sink.
    ext.createRealFileSink = function(name, fileName) {
        if (this._checkComponentAbsent(name)) {
            this._sendCommand("CREATE REAL-FILE-SINK " + name + " " + fileName);
            this._connectDataSink(name);
        }
    }

    // Block for creating the real valued file source.
    ext.createRealFileSource = function(name, fileName) {
        if (this._checkComponentAbsent(name)) {
            this._sendCommand("CREATE REAL-FILE-SOURCE " + name + " " + fileName + " " + sampleRate);
            this._connectDataSource(name);
        }
    }

    // Block for creating a new low pass filter.
    ext.createLowPassFilter = function(name, bandwidth) {
        if (this._checkComponentAbsent(name)) {
            this._sendCommand("CREATE LOW-PASS-FILTER " + name + " " +
                ((bandwidth * 2000) / sampleRate));
            this._connectDataProcessor(name);
        }
    }

    // Block for creating a new band pass filter.
    ext.createBandPassFilter = function(name, lowCutoff, highCutoff) {
        if (this._checkComponentAbsent(name)) {
            this._sendCommand("CREATE BAND-PASS-FILTER " + name + " " +
                ((lowCutoff * 2000) / sampleRate) + " " +
                ((highCutoff * 2000) / sampleRate));
            this._connectDataProcessor(name);
        }
    }

    // Block for creating a simple connection from an existing data producer.
    ext.makeSimpleConnection = function(producer) {
        if (this._checkComponentPresent(producer)) {
            this._connectDataSource(producer);
        }
    }

    // Send a fixed message over the radio.
    ext.sendSimpleMessage = function(message) {
        this._sendMessage(message);
    }

    // Receive a message over the radio.
    ext.receiveSimpleMessage = function(callback) {
        this._receiveMessage(callback);
    }

    // Receive an error message.
    ext.receiveErrorMessage = function(callback) {
        errorCallbacks.push(callback);
    }

    // Block and block menu descriptions
    var descriptor = {
        blocks: [
            // Block type, block name, function name
            [' ', 'reset radio', 'radioReset'],
            [' ', 'start radio', 'radioStart'],
            [' ', 'stop radio', 'radioStop'],
            ['b', 'radio running', 'isRadioRunning'],
            [' ', 'send message %s', 'sendSimpleMessage', 'Hello World'],
            ['R', 'receive message', 'receiveSimpleMessage'],
            ['R', 'receive error', 'receiveErrorMessage'],
            [' ', '\u2533 radio source %s at %n MHz', 'createRadioSource', 'lime-source', 433],
            [' ', '\u2533 message source %s', 'createMessageSource', 'tx-message'],
            [' ', '\u2533 source %s from file %s', 'createRealFileSource', 'sample-source', 'file-name'],
            [' ', '\u2513 source data from %s', 'makeSimpleConnection', 'producer'],
            [' ', '\u253B radio sink %s at %n MHz', 'createRadioSink', 'lime-sink', 433],
            [' ', '\u253B display sink %s', 'createDisplaySink', 'spectrum'],
            [' ', '\u253B message sink %s', 'createMessageSink', 'rx-message'],
            [' ', '\u253B sink %s to file %s', 'createRealFileSink', 'sample-sink', 'file-name'],
            [' ', '\u2503 simple framer %s', 'createSimpleFramer', 'tx-framer'],
            [' ', '\u2503 simple deframer %s', 'createSimpleDeframer', 'rx-deframer'],
            [' ', '\u2503 Manchester encoder %s', 'createManchesterEncoder', 'mcr-encoder'],
            [' ', '\u2503 Manchester decoder %s', 'createManchesterDecoder', 'mcr-decoder'],
            [' ', '\u2503 OOK modulator %s at %n KHz', 'createOokModulator', 'ook-modulator', 50],
            [' ', '\u2503 OOK demodulator %s', 'createOokDemodulator', 'ook-demodulator'],
            [' ', '\u2503 bit rate sampler %s', 'createBitRateSampler', 'bit-sampler'],
            [' ', '\u2503 low pass filter %s with bandwidth %n KHz', 'createLowPassFilter', 'lp-filter', 100],
            [' ', '\u2503 band pass filter %s with pass band %n KHz to %n KHz', 'createBandPassFilter', 'bp-filter', 47, 53],
        ]
    };

    // Register the extension
    ScratchExtensions.register('Lua Radio Extension', descriptor, ext);
})({});
