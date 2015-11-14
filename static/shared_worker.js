self.addEventListener("connect", function (event) {

	var port = event.ports[0],
        ws = new WebSocket("ws://localhost:7777/websocket"); //todo сделать инициализацию и общим объектом для страничек

    ws.onopen = function(event) {
        ws.send(JSON.stringify({client_id: 777})); //todo передавать при инициализации
        port.postMessage(JSON.stringify({connection: 'web socket opend'}));
    }

    ws.onmessage = function(event) {
        port.postMessage(event.data)
    }

    ws.onerror = function(event) {
        port.postMessage('error');
    }

	port.addEventListener("message" , function (event) {
        ;
	}, false);

	port.start();

}, false);