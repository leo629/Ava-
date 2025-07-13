// chat.js
let chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/' + user + '/'
);

chatSocket.onmessage = function(e) {
    let data = JSON.parse(e.data);
    let message = data['message'];
    let sender = data['sender'];

    // Append the message to the chat box
    document.querySelector('#chat-box').innerHTML += `<p><strong>${sender}:</strong> ${message}</p>`;
};

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};

// Function to send a message
document.querySelector('#send-button').onclick = function(e) {
    let messageInput = document.querySelector('#message-input');
    let message = messageInput.value;
    chatSocket.send(JSON.stringify({
        'message': message,
        'receiver': otherUser // Define the receiver's username here
    }));
    messageInput.value = ''; // Clear the input field
};

if (chatSocket.readyState === WebSocket.OPEN) {
    chatSocket.send(JSON.stringify({
        message: message,
        receiver: "{{ other_user.username }}"
    }));
} else {
    console.error("WebSocket is not open. Current state: " + chatSocket.readyState);
}


function connectSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/chat/{{ other_user.username }}/`);
    
    socket.onopen = function() {
        console.log("WebSocket connected");
    };

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        // Handle incoming message
    };

    socket.onclose = function(event) {
        console.log("WebSocket closed. Attempting to reconnect...");
        setTimeout(connectSocket, 3000); // Attempt reconnect after 3 seconds
    };

    return socket;
}

let chatSocket = connectSocket();
