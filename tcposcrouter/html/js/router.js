
function connect() {
    let ws;
    var host = window.location.hostname;
    
    if (!host) {
        host = "localhost";
    }

    if (location.protocol === 'https:') {
        ws = new WebSocket("wss://" + host + ":5681/");
    } else {
        ws = new WebSocket("ws://" + host + ":5681/");
    }
    let messages = document.querySelector("#messages");
    let users = document.querySelector("#users");
    let n_users = document.querySelector("#n_users");

    ws.onmessage = function (event) {
        var currentdate = new Date();
        var datetime = '[' + currentdate.getDate() + "/"
                    + (currentdate.getMonth()+1)  + "/"
                    + currentdate.getFullYear() + " @ "
                    + currentdate.getHours() + ":"
                    + currentdate.getMinutes() + ":"
                    + currentdate.getSeconds() + '] ';
        var json_data = JSON.parse(event.data);
        if (json_data.messages != null) {
            json_data.messages.forEach(function(msg_json) {
                var message = document.createElement('li');
                var msg = "User '" + msg_json['user'] + "' sent to address '" + msg_json['address'] + "' with args: '" + msg_json['args'] + "'";
                message.textContent = datetime + msg; 
                messages.insertBefore(message, messages.childNodes[0]);
            });
        };

        if (json_data.users != null) {
            n_users.textContent = Object.keys(json_data.users).length;
            users.textContent = "";
            console.log(json_data);
            Object.keys(json_data.users).sort(function (a, b) {return a.toLowerCase().localeCompare(b.toLowerCase())}).forEach( function(user){
                var user_el = document.createElement('li');
                user_el.textContent = user + "[" + json_data.users[user].length  + "]";
                users.appendChild(user_el);
            });
        };
    };

    ws.onclose = function(e) {
        setTimeout(function() {
          connect();
        }, 1000);
    };

    ws.onerror = function(err) {
        //console.error('Socket encountered error: ', err.message, 'Closing socket');
        ws.close();
    };
};

connect();
