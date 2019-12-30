import socket
from websocket import WebSocketApp

ScratchLinkWebSocket = 'wss://localhost:20110/scratch/blepingpong'


class BLEPINGPONG(WebSocketApp):

    '''
     * A BLEPINGPONG peripheral socket object.  It handles connecting, over web sockets, to
     * BLEPINGPONG peripherals, and reading and writing data to them.
     * @param {Runtime} runtime - the Runtime for sending/receiving GUI update events.
     * @param {string} extensionId - the id of the extension using this socket.
     * @param {object} peripheralOptions - the list of options for peripheral discovery.
     * @param {object} connectCallback - a callback for connection.
     * @param {object} disconnectCallback - a callback for disconnection.
    '''
    def __init__(self, runtime, extensionId, peripheralOptions, connectCallback, disconnectCallback = None, \
            connectCount1 = False):
        ws = WebSocketApp(ScratchLinkWebSocket, on_error=self._handleRequestError, on_close=handleDisconnectError)
        self = ws.super()

        self._ws = ws
        self._ws.onopen = self.requestPeripheral.bind(self) # only call request peripheral after socket opens
        self._ws.onerror = self._handleRequestError.bind(self, 'ws onerror')
        self._ws.onclose = self.handleDisconnectError.bind(self, 'ws onclose')

        self._availablePeripherals = {}
        self._connectCallback = connectCallback
        self._connected = false
        self._characteristicDidChangeCallback = null
        self._disconnectCallback = disconnectCallback
        self._discoverTimeoutID = null
        self._extensionId = extensionId
        self._peripheralOptions = peripheralOptions
        self._runtime = runtime
        self._connectCount1 = connectCount1

    constructor (runtime, extensionId, peripheralOptions, connectCallback, disconnectCallback = null, connectCount1 = false) {
        const ws = new WebSocket(ScratchLinkWebSocket);
        super(ws);

        this._ws = ws;
        this._ws.onopen = this.requestPeripheral.bind(this); // only call request peripheral after socket opens
        this._ws.onerror = this._handleRequestError.bind(this, 'ws onerror');
        this._ws.onclose = this.handleDisconnectError.bind(this, 'ws onclose');

        this._availablePeripherals = {};
        this._connectCallback = connectCallback;
        this._connected = false;
        this._characteristicDidChangeCallback = null;
        this._disconnectCallback = disconnectCallback;
        this._discoverTimeoutID = null;
        this._extensionId = extensionId;
        this._peripheralOptions = peripheralOptions;
        this._runtime = runtime;
        this._connectCount1 = connectCount1;
    }
