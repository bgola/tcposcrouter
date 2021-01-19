g = OSCRouterClient(\userName, \group, userPassword: \userPw, groupPassword: \groupw);
g.join( { g.sendMsg(\test, 123)} );
