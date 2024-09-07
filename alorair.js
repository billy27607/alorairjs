const readline = require('readline');
const { exec } = require('child_process');
const can = require('socketcan');

//humidifir state
const humidifier = {
    power: false,
    running: false,
    pumpRunning: false,
    targetHumidity: 0,
    humidity: 0,
    temperature: 0
};

//We want to ignore return messages excpt for status requests
let isStatus = false;

// CAN channel
const channel = can.createRawChannel('can0', true);
channel.start();

// Define the message handler
channel.addListener('onMessage', (msg) => {
    if (!isStatus) {
        return;
    }
    isStatus = false;
    // console.log('Received CAN message:', msg);
    const bit1 = (msg.data[5] & 0b1) !==0;
    const bit2 = (msg.data[5] & 0b10) !==0;
    const pumpRunning = (msg.data[5] & 0b10000) !==0;

    humidifier.power = !!(bit1 | bit2);
    humidifier.running = bit1;
    humidifier.pumpRunning = pumpRunning;
    humidifier.targetHumidity = msg.data[1];
    humidifier.humidity = msg.data[0];
    humidifier.temperature = (msg.data[3] * 9 / 5) + 32;


    console.log('humidifier status');
    console.log(humidifier);


    promptUser();
});

// send the commands
const send = (dataPayload) => {
    let message = {
        id: 0x123,
        ext: false, // Standard frame
        data: Buffer.from(dataPayload)
    };
    // if (dataPayload.length > 1) {
    //     ignoreNextMessage = true;
    // }
    channel.send(message);
}

// commandline interface
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

const promptUser = () => {
    rl.question('>>>> ', async (input) => {
        const [command, arg] = input.trim().toLowerCase().split(' ');

        try {
            await executeCommand(command, arg);
        } catch (error) {
            console.error('Command failed:', error);
        } finally {
            // Prompt for the next command
            promptUser();
        }
    });
};

const executeCommand = (command, arg) => {
    return new Promise((resolve, reject) => {
        switch (command) {
            case 'status':
                console.log('Fetching status...');
                isStatus = true;
                send([0x01]);
                resolve();
                break;
            case 'poweron':
                console.log('Powering on...');
                send([0x01, 0x01, 0x01]);
                resolve();
                break;
            case 'poweroff':
                console.log('Powering off...');
                send([0x01, 0x01, 0x00]);
                resolve();
                break;
            case 'set_target_humidity':
                if (!arg || isNaN(arg)) {
                    console.log('Please provide a valid numeric value for target humidity.');
                    resolve();
                    break;
                }
                console.log(`Setting target humidity to ${arg}%...`);
                send([0x01, 0x05, arg])
                resolve();
                break;
            case 'pumpout':
                console.log('Pumping out...');
                send([0x01, 0x02, 0x01]);
                resolve();
                break;
            case 'initialize_can':
                console.log('Initializing CAN bus...');
                exec('sudo ip link set can0 down', (error, stdout, stderr) => {
                    if (error) {
                        reject(`Error: ${error.message}`);
                        return;
                    }
                    if (stderr) {
                        reject(`stderr: ${stderr}`);
                        return;
                    }
                    console.log(stdout);
                    resolve();
                });
                exec('sudo ip link set can0 up type can bitrate 50000', (error, stdout, stderr) => {
                    if (error) {
                        reject(`Error: ${error.message}`);
                        return;
                    }
                    if (stderr) {
                        reject(`stderr: ${stderr}`);
                        return;
                    }
                    console.log(stdout);
                    resolve();
                });
                const channel = can.createRawChannel('can0', true);
                channel.start();
                break;
            case 'q':
            case 'exit':
                rl.close();
                break;
            default:
                console.log(`Unknown command: ${command}`);
                resolve();
        }
    });
};

promptUser();

rl.on('close', () => {
    console.log('Exiting...');
    process.exit(0);
});
