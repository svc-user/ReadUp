from quart import Quart, websocket, send_from_directory
import uuid
import json
import core  # Assuming the readup module is available

app = Quart(__name__)

# Serve the static index.html
@app.route('/')
async def index():
    return await send_from_directory('static', 'index.html')

@app.route('/stream/<string:path>')
async def stream_file(path):
    return await send_from_directory('articles', path)

# WebSocket endpoint
@app.websocket('/ws')
async def ws():
    while True:
        try:
            # Wait for the client to send a message with the URL and config
            message = await websocket.receive()
            data = json.loads(message)

            url = data.get('url')
            config = data.get('config')

            if not url:
                await websocket.send(json.dumps({"error": "Invalid input. URL is required."}))
                return

            async def handler(chunk):
                await websocket.send_json(chunk) # _send is just a proxy call to ASGIWebsocketConnection.send_data 

            await core.do_heavy_lifting(url, handler)

            await websocket.send_json({"done": "done"})


        except Exception as e:
            await websocket.send(json.dumps({"error": str(e)}))



if __name__ == '__main__':
    app.run(debug=False, port=1235, host="0.0.0.0", threaded=True, use_reloader=False)
