const can = require('socketcan');
const net = require('net');

// Create CAN channel
const channel = can.createRawChannel('can0', true);

// Create TCP client
const client = new net.Socket();
client.connect(41234, '192.168.1.2', () => {
    console.log('Connected to receiver');
});

// Send CAN message over TCP
channel.addListener('onMessage', (msg) => {
    const message = JSON.stringify(msg);
    client.write(message);
});

channel.start();
