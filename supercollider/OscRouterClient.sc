OscRouterClient {
	var <serveraddress, <username, <password, <onConnect,
	<groupname, <grouppassword,
	<serverport, <tcpRecvPort, <responders,
	<pid, <netAddr, <id,
	<peers, <peerWatcher,
	authenticated;


	*new {arg serveraddress, username, password, onConnect, groupname, grouppassword, serverport = 55555;
		^super.newCopyArgs(serveraddress, username, password, onConnect, groupname, grouppassword, serverport).init;
	}

	init {
		responders = ();
		peers = Set();
		authenticated = false;
		ShutDown.add({this.close});
	}

	join {
		arg onSuccess, onFailure;
		var portResponder, randomId, registerChecker;
		randomId = 999999.rand;

		portResponder = {|...msg|
			if (msg[0][0].asString == ('/oscrouter/register/' ++ username ++ '/' ++ randomId).asString, {
				tcpRecvPort = msg.last;
				this.confirmJoin;
				registerChecker.stop;
				thisProcess.removeOSCRecvFunc(portResponder);
				onConnect.value(this);
			});
		};


		registerChecker = Task({
			3.wait;
			("Can't connect or auth with " ++ serveraddress).postln;
			thisProcess.removeOSCRecvFunc(portResponder);
		});

		thisProcess.addOSCRecvFunc(portResponder);
		netAddr = NetAddr(serveraddress, serverport);
		netAddr.tryConnectTCP({
			netAddr.notNil.if({
				netAddr.isConnected.if({
					netAddr.sendMsg('/oscrouter/register', username, password, randomId);
					registerChecker.play;
					onSuccess.notNil.if({onSuccess.value});
					peerWatcher = OSCFunc({ |msg|
						peers = msg[1..];
					}, '/oscrouter/userlist');
				});
			});
		}, {
			("Failed to connect to " ++ serveraddress).postln;
			onFailure.notNil.if({onFailure.value});
		});
	}

	tryToReconnect { arg msg;
		var responder_funcs = ();
		var joined = false;
		responders.do({arg oscfunc, id; responder_funcs.add(id -> oscfunc.func)});
		this.close;
		"Trying to reconnect...".postln;
		fork {
			var retries = 5;
			{(joined.not).and(retries > 0)}.while {
				this.join({
					var counter=0;
					joined = true;
					// waits 3 seconds for the registering confirmed and then send again
					{(counter < 30).and(authenticated.not)}.while({
						0.5.wait;
						counter = counter + 1;
					});

					authenticated.if({
						// Recover all responder functions and add them again to the new
						// TCP receive port
						responder_funcs.do({|func, id| this.addResp(id, func)});
						"Reconnect success! resending message...".postln;
						netAddr.sendMsg(*msg);

					}, {
						"Failed to reconnect, giving up...".postln;
					});
				});
				5.wait;
				retries = retries - 1;
			};
			joined.not.if { "5 attempts to reconnect failed, giving up!" };
		};
	}

	enablePing {
		SystemClock.sched(3.0, {
			authenticated.if({
				this.sendMsg("/oscrouter/ping", username);
				3.0;
			}, {
				nil;
			});
		});
	}

	cmdPeriod {
		this.enablePing;
	}

	confirmJoin {
		("Connected to " ++ serveraddress).postln;
		("    receiving on port " ++ tcpRecvPort).postln;
		authenticated = true;
		CmdPeriod.add(this);
		this.enablePing;
	}

	close {
		var keys;
		authenticated = false;
		"closing".postln;
		netAddr.isConnected.if({netAddr.tryDisconnectTCP});
		keys = responders.keys;
		keys.do({arg id; this.removeResp(id)});
		responders = ();
		CmdPeriod.remove(this);
	}

	sendMsg { arg ... msg;
		msg[0] = this.formatSymbol(msg[0]);
		// tries to send the message, if failed, tries to reconnect if for some reason
		// the connection is lost
		{netAddr.sendMsg(*msg)}.try({this.tryToReconnect(msg)})
	}

	sendMsgToUser { arg ... args;
		var username = args[0];
		peers.find([username]).notNil.if({
			this.sendMsg('/oscrouter/private', username, *args[1..]);
		}, {
			"Don't know user".postln;
		});
	}

	sendMsgArray {arg symbol, array;
		symbol = this.formatSymbol(symbol);
		netAddr.sendMsg(symbol, *array)
	}

	addResp { arg id, function, permanent = true;
		netAddr.isConnected.if({
			// there are two ways to pass in the symbol id... fix it here
			id = this.formatSymbol(id);
			responders[id].notNil.if({this.removeResp(id)});
			responders.add(id -> OSCFunc(function, id, recvPort: tcpRecvPort).permanent_(permanent));
		}, {
			"You must register your client with .join on a Server before you add a responder".warn
		})
	}

	removeResp {arg id;
		id = this.formatSymbol(id);
		responders[id].free;
		responders[id] = nil;
	}

	formatSymbol {arg symbol;
		var str;
		str = symbol.asString;
		(str[0] == $/).if({
			^str.asSymbol;
		}, {
			^("/"++str).asSymbol
		})
	}

}
