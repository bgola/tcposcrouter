let known_users = {};
let soundOn = false;
let gData = {
  nodes: [],
  links: []
};

let Graph = ForceGraph3D()
      (document.getElementById('3d-graph'))
        //.nodeColor(node => 'white')
        .backgroundColor('white')
        .enableNodeDrag(true)
        //.nodeOpacity(0.5)
        .nodeAutoColorBy('group')
		.nodeThreeObject(node => {
          // use a sphere as a drag handle
          const obj = new THREE.Mesh(
            new THREE.SphereGeometry(10),
            new THREE.MeshBasicMaterial({ depthWrite: false, transparent: true, opacity: 0 })
          );

          // add text sprite as child
          const sprite = new SpriteText(node.id);
          sprite.color = node.color;
          sprite.textHeight = 8;
          obj.add(sprite);

          return obj;
        })
        .linkDirectionalParticleColor(() => 'red')
        .linkDirectionalParticleWidth(2)
        .graphData(gData);

Graph.d3Force('charge').strength(-890);

function update_graph() {
    var all_nodes = [];
    var links= [];
    
    // removes any particles left, i guess its a bug in 3d-force-graph
    Graph.graphData().links.forEach(link => {
        if (link.__singleHopPhotonsObj) {
            link.__singleHopPhotonsObj.children.forEach( el => {
                link.__singleHopPhotonsObj.remove(el)
            });
        };
    });
    
    Object.keys(known_users).forEach(function (name) {
        all_nodes.push({'id': name, group: name, type: 'user'});
        known_users[name].connections.forEach(function (conn, idx) {
            all_nodes.push({'id': conn.toString(), group: name, type: 'connection'});
            links.push({source: conn.toString(), target: name});
        });
    });
    
    all_nodes.filter(node => node.type == 'user').forEach(u1 => {
        all_nodes.filter(node => node.type =='user').forEach(u2 => {
            if (u1 != u2) {
                links.push({source: u1.id, target: u2.id});
            };
        });
    });

    gData = {
        nodes: all_nodes,
        links: links
    };
    Graph.graphData(gData);

    Graph.graphData().nodes.forEach(function (node) {
        if (node.type == 'user') {
            known_users[node.id].node = node;
        };
    });
};

function update_user(user, user_data) {
    known_users[user]['connections'] = user_data;
    update_graph();
    if (soundOn) {
       update_sound(user);
    };
};

function new_user(user, user_data) {
    known_users[user] = {'name': user, 'connections': user_data};
    update_graph();
    if (soundOn) {
        initialize_sound(user);
    };
};


function update_sound(user) {
    var u = known_users[user];
    if (u.node.__threeObj) {
        u.panner.updatePosition(u.node.__threeObj);
    };
};

function initialize_sound(user) {
    var u = known_users[user];
    u.panner = new Tone.Panner3D().toMaster();
    u.panner.panningModel = "equalpower";
    u.panner.refDistance = 40;
    u.panner.rollofFactor = 0.9;
    if (u.node.__threeObj) {
        u.panner.updatePosition(u.node.__threeObj);
    };
    var r = Math.floor(Math.random()*5);
    switch (r) {
        case 0:
            u.synth = new Tone.MembraneSynth().connect(u.panner);
            break;
        case 1:
            u.synth = new Tone.FMSynth().connect(u.panner);
            break;
        case 2:
            u.synth = new Tone.MetalSynth().connect(u.panner);
            break;
        case 3:
            u.synth = new Tone.PluckSynth().connect(u.panner);
            break;
        case 4:
            u.synth = new Tone.MonoSynth().connect(u.panner);
            break;
    };  
    u.node.__threeObj.addEventListener("change", () => updateSound());
};

function destroy_sound(user) {
    var u = known_users[user];
    u.panner.dispose();
    u.panner = null;
};

function play_sound(user, msg) {
    var u = known_users[user];

    if(u.synth == null)
        return;
    
    var scale = [ 1.0, 1.1224620483089, 1.2240535433037, 1.3348398541685, 1.4983070768743, 1.6817928305039, 1.8340080864049 ];
    var octaves = [1, 2, 4, 8];
    var base_freq = 50;
    var freq = base_freq * scale[Math.floor(Math.random() * scale.length)] * octaves[Math.floor(Math.random()*octaves.length)];
    var length = msg.address.length;
    msg.args.forEach(arg => length += arg.toString().length);
    u.synth.triggerAttackRelease(freq, Math.min(length/1000.0, 2.0));
};

function remove_user(user) {
    if (soundOn) {
        destroy_sound(user);
    };

    delete known_users[user];
    update_graph();
};

function connect() {
    let ws;
    if (location.protocol === 'https:') {
        ws = new WebSocket("wss://bgo.la:5681/");
    } else {
        ws = new WebSocket("ws://localhost:5681/");
    }

    ws.onmessage = function (event) {
        var json_data = JSON.parse(event.data);
        if (json_data.messages != null) {
            json_data.messages.forEach(function(msg_json) {
                var msg = "User '" + msg_json['user'] + "' sent to address '" + msg_json['address'] + "' with args: '" + msg_json['args'] + "'";
                Graph.graphData().links.forEach(function (link) {
                    if (link.source.id == msg_json.user && Object.keys(known_users).includes(link.target.id)) {
                        Graph.emitParticle(link);
                    };
               });
                if (Object.keys(known_users).includes(msg_json.user)) {
                    play_sound(msg_json.user, msg_json);
                }
           });
        };

        if (json_data.users != null) {
            console.log(json_data.users);
            n_users = Object.keys(json_data.users).length;
            Object.keys(json_data.users).forEach( function(user){
                if (known_users[user] != null) {
                    update_user(user, json_data.users[user]);
                } else {
                    new_user(user, json_data.users[user]);
                };
            });

            Object.keys(known_users).forEach( function(user){
                if (json_data.users[user] == null) {
                    remove_user(user);
                };
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

function updateSound() {
    Object.keys(known_users).forEach(user => known_users[user].panner.updatePosition(known_users[user].node.__threeObj));
    Tone.Listener.updatePosition(Graph.camera());
};

function startSound() {
    soundOn = true;
    Tone.context.resume();
    Object.keys(known_users).forEach(u => initialize_sound(u));
    Tone.Listener.updatePosition(Graph.camera());
    Graph.controls().addEventListener("change", () => updateSound());
};

document.querySelector("#play").onclick = function () {
    document.querySelector("#play").remove();
    startSound();
};
connect();
