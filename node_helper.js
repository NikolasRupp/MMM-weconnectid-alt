var NodeHelper = require("node_helper");
const spawn = require("child_process").spawn;
const once = require("events").once
const path = require("path")
const exec = require('child_process').exec

module.exports = NodeHelper.create({

    init() {
    },

    start() {
    },

    stop() {
    },

    // If notification of the main.js file is received, the node_helper will do this here:
    socketNotificationReceived(notification, payload) {
        if (notification === "DO_PYTHON") {
            this.config = payload
            this.api();
        } else {
            console.log(this.name + " received a socket notification: " + notification + " - Payload: " + payload);
        }
    },

	api() {
	    var self = this;
    	let handler
		handler = spawn(this.config.python, ["-u",__dirname+path.sep+"api.py",this.config.username,this.config.password,this.config.vin]);
		handler.stdout.on('data', (data) => {
			console.log("Got data from weconnectid for VIN " + this.config.vin)
			this.sendSocketNotification("PYTHON_DONE", data.toString())
		})
	}
});
