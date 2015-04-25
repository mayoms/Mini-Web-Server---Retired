__author__ = 'micah'

import socket
import os
import pprint

PATH = 'sites'

RESPONSE_CODES = {
	'200': b"HTTP/1.1 200 OK\r\nServer: My Little Server\r\nContent-Type:text\html\r\n\n",
	'404': b"HTTP/1.1 404 Not Found\r\n\n404 Page Not Found",
	'301': b"HTTP/1.1 301 Redirect\r\nLocation: ",
	'501': b"HTTP/1.1 501 Not Implemented\r\n\nNot Implemented Yet",
	'400': b"HTTP/1.1 400 Bad Request\r\n\nUnable to Parse Header",
}

class WebServer(object):

	def __init__(self, ipaddr, port):

		self.ipaddr = ipaddr
		self.port = port
		self.sock = None
		self.client = None
		self.clientaddr = None
		self.log = None

	def run_server(self):

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		self.sock.bind((self.ipaddr, self.port))
		self.sock.listen(socket.SOMAXCONN)

		while True:
			self.client, self.addr = self.sock.accept()
			data = self.client.recv(4096)
			if data:
				self.client.sendall(bytes(self.http_response(data.decode('utf-8'))))
			self.client.close()
		self.socket.close()

	def parse_header(self,request_header):
		try:	
			request_header = request_header.split('\r\n')
			request_header[0] = request_header[0].split(' ')
			parsed_request = {}
			parsed_request['request_method'] = request_header[0][0]
			parsed_request['request_path'] = request_header[0][1]
			parsed_request['headers'] = {}
			for item in request_header[1:]:
				if item:
					item = item.split(':')
					parsed_request['headers'][item[0]] = item[1]
			return parsed_request
		except (IndexError, KeyError):
			return None

	def http_response(self, http_request):

		header_data = self.parse_header(http_request)
		if header_data:
			if header_data['request_method'] == 'GET':
				page = self.fetch_resource(header_data['request_path'])
				return page
			if header_data['request_method'] == 'HEAD':
				return RESPONSE_CODES['200']
			return RESPONSE_CODES['501']
		return RESPONSE_CODES['401']
		print("Sending 401")


	def fetch_resource(self, path):
		try: 
			with open(os.path.join(PATH+path,'index.html'), 'rb') as fh:
				return RESPONSE_CODES['200'] + fh.read()
		except FileNotFoundError:
			return RESPONSE_CODES['404']

def main():
	webserver = WebServer('0.0.0.0', 3000)
	webserver.run_server()


if __name__ == '__main__':
	main()


