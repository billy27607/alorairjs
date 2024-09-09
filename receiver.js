const can = require('socketcan');
const net = require('net');

// Create CAN channel
const channel = can.createRawChannel('can0', true);

// Create TCP server
const server = net.createServer((socket) => {
    socket.on('data', (data) => {
        const msg = JSON.parse(data);
        channel.send(msg);
    });
});

server.listen(41234, '0.0.0.0', () => {
    console.log('Server listening on port 41234');
});

channel.start();
