~server = "127.0.0.1"

~user1 = OscRouterClient.new(~server, "user1", "user1pw");
~user1.join

// it is possible to specify a function to be called when the connection is successful
// but note that you need to call join to connect
~user2 = OscRouterClient.new(~server, "user2", "user2pw", {|router| "success!".postln;});

// should print "success!" when join
~user2.join;

// register an echo replier
~user1.addResp('/echo', {|msg, time, addr, recvPort| "user1: ".post; msg.postln});

// sends an echo message, but no one else is listening
~user1.sendMsg('/echo', "test", 1, 2, 3);

// if another user sends the /echo, then we see it
~user2.sendMsg('/echo', "test", 1, 2, 3);

// there is a ping message, but i think we can implement this in other ways, we dont
// need ping with the TCP connection
~user1.addResp('/oscrouter/ping', {|msg, time, addr, recvPort| "user1 got ping from ".post; msg[1].postln});
~user2.addResp('/oscrouter/ping', {|msg, time, addr, recvPort| "user2 got ping from ".post; msg[1].postln});

// another user join, we should get pings from it
~user3 = OscRouterClient.new(~server, "user3", "user3pw");
~user3.join;
