# host a local server to serve the web app
import http.server
import socketserver
import settings

PORT = 8000
DATA_PATH = settings.DATA_PATH

Handler = http.server.SimpleHTTPRequestHandler

# Host a local server with directory set to DATA_PATH
class CustomHandler(Handler):
    def translate_path(self, path):
        # Override the translate_path method to serve files from DATA_PATH
        path = super().translate_path(path)
        relpath = path[len(self.directory):]
        return DATA_PATH + relpath

# Create the server with the custom handler
with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()



