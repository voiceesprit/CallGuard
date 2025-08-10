const WebSocket = require('ws');

const wss = new WebSocket.Server({ port: 3000 });

let clients = [];

wss.on('connection', function connection(ws) {
  clients.push(ws);
  console.log('Client connected. Total clients:', clients.length);

  ws.on('message', function incoming(message) {
    // Broadcast the received message to all other clients (including yourself if you want loopback)
    // For loopback test, you can send back to the sender
    // Here, we'll send back to all clients except sender:

    clients.forEach(client => {
      if (client !== ws && client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });

    // For a loopback test, uncomment below to send message back to sender as well:
    // if (ws.readyState === WebSocket.OPEN) {
    //   ws.send(message);
    // }
  });

  ws.on('close', () => {
    clients = clients.filter(client => client !== ws);
    console.log('Client disconnected. Total clients:', clients.length);
  });
});

console.log('Signaling server running on ws://localhost:3000');