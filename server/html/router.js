let ws;

if (location.protocol === 'https:') {
    ws = new WebSocket("wss://bgo.la:5680/");
} else {
    ws = new WebSocket("ws://localhost:5680/");
}
let messages = document.querySelector("#messages");
let users = document.querySelector("#users");
ws.onmessage = function (event) {
    var currentdate = new Date();
    var datetime = '[' + currentdate.getDate() + "/"
                + (currentdate.getMonth()+1)  + "/"
                + currentdate.getFullYear() + " @ "
                + currentdate.getHours() + ":"
                + currentdate.getMinutes() + ":"
                + currentdate.getSeconds() + '] ';
    console.log(event.data);
    if (event.data[0] == "m") {
        var message = document.createElement('li');
        message.textContent = datetime + event.data.substr(1);
        messages.insertBefore(message, messages.childNodes[0]);
    } else {
        var userlist = event.data.substr(1).split(",").sort();
        users.textContent = "";
        for (i=0; i<userlist.length; i++) {
            var user = document.createElement('li');
            user.textContent = userlist[i];
            users.appendChild(user);
        };
    };
};
