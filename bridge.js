const can = require('socketcan');
const net = require('net');

// CAN channel setup
const canChannel = can.createRawChannel('can0', true);
canChannel.start();

// TCP server setup
const server = net.createServer((socket) => {
    console.log('Client connected');

    // Forward CAN messages to TCP client
    canChannel.addListener('onMessage', (msg) => {
        socket.write(msg.data);
    });

    // Forward TCP messages to CAN bus
    socket.on('data', (data) => {
        const message = {
            id: 0x123,
            ext: false,
            data: Buffer.from(data)
        };
        canChannel.send(message);
    });

    socket.on('end', () => {
        console.log('Client disconnected');
    });
});

server.listen(3000, () => {
    console.log('TCP server listening on port 3000');
});

// TCP client setup
const client = new net.Socket();
client.connect(3000, 'remote_raspberry_pi_ip', () => {
    console.log('Connected to server');

    // Forward CAN messages to TCP server
    canChannel.addListener('onMessage', (msg) => {
        client.write(msg.data);
    });

    // Forward TCP messages to CAN bus
    client.on('data', (data) => {
        const message = {
            id: 0x123,
            ext: false,
            data: Buffer.from(data)
        };
        canChannel.send(message);
    });

    client.on('close', () => {
        console.log('Connection closed');
    });
});
