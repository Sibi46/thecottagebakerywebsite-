import http.server
import os
import json
import base64

PORT = 8080
# Simple username and password for deployment
USERNAME = "admin"
PASSWORD = "password123" 

class AdminHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def check_auth(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header:
            return False
        
        expected = 'Basic ' + base64.b64encode(f'{USERNAME}:{PASSWORD}'.encode('utf-8')).decode('utf-8')
        return auth_header == expected

    def request_auth(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Admin Access"')
        self.end_headers()
        self.wfile.write(b'Authentication required')

    def do_GET(self):
        # Protect the admin panel and the images API
        if self.path.startswith('/admin.html') or self.path.startswith('/api/images'):
            if not self.check_auth():
                self.request_auth()
                return

        if self.path == '/api/images':
            # List all image files in the current directory
            valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
            try:
                files = [f for f in os.listdir('.') if os.path.isfile(f) and f.lower().endswith(valid_extensions)]
            except Exception as e:
                files = []
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(files).encode('utf-8'))
            return
            
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/upload':
            # Protect upload endpoint
            if not self.check_auth():
                self.request_auth()
                return

            file_name = self.headers.get('X-File-Name')
            content_length = int(self.headers.get('Content-Length', 0))
            
            if not file_name or content_length == 0:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Missing filename or content details')
                return

            try:
                # Security: prevent directory traversal
                safe_name = os.path.basename(str(file_name))
                
                # Read binary file data from request body
                file_data = self.rfile.read(content_length)
                
                # Overwrite existing file or write new one
                with open(safe_name, 'wb') as f:
                    f.write(file_data)
                    
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "File updated successfully"}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return
            
        self.send_response(404)
        self.end_headers()

class AdminHTTPServer(http.server.HTTPServer):
    allow_reuse_address = True

with AdminHTTPServer(("", PORT), AdminHTTPRequestHandler) as httpd:
    print(f"Serving at http://localhost:{PORT}")
    print(f"Go to http://localhost:{PORT} to view the site.")
    print(f"Go to http://localhost:{PORT}/admin.html to manage images.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
