__author__ = 'micah'

import socket
import os
import subprocess
import re

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
		self.site_options = {}

	def load_site_options(self):
		try:
			with open(os.path.join(PATH,'.siteoptions'),'r') as fh:
				for line in fh.readlines():
					if line.strip() and line[0] is not '#':
						line = line.split()
						self.site_options[line[0]] = line[1:]
		except FileNotFoundError:
			print('Site options not found.')
			self.site_options['index'] = ('index.html','1')

	def run_server(self):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		sock.bind((self.ipaddr, self.port))
		sock.listen(socket.SOMAXCONN)

		while True:
			client, addr = sock.accept()
			data = client.recv(4096)
			if data:
				client.sendall(bytes(self.http_response(data.decode('utf-8'))))
			client.close()
		socket.close()

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

	def parse_path(self,request_path):
		parsed_path = {}
		parsed_path['path'], parsed_path['resource'] = request_path.rsplit('/',1) 
		if '?' in parsed_path['resource']:
			#Problem is here
			parsed_path['resource'], parsed_path['arguments'] = self.unquote(parsed_path['resource'].replace('+',' ')).split('?')
		else:
			parsed_path['arguments'] = None
		return parsed_path



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


	def fetch_resource(self, request_path):
		resource_data = None
		if request_path == '/':
			self.load_site_options()
			print(self.site_options)
			if self.site_options:
				if self.site_options['index'][1] == '0':
					resource_data = self.run_script(request_path, self.site_options['index'][0])
				else:
					resource_data = self.load_document(request_path, self.site_options['index'][0])
		else:
			request_path = self.parse_path(request_path)
			print(request_path)
			if '.htm' in request_path['resource'][-5:]:
				resource_data = self.load_document(request_path['path'], request_path['resource'])
			else:
				resource_data = self.run_script(request_path['path'], request_path['resource'], arguments=request_path['arguments'])
		if resource_data:
			return RESPONSE_CODES['200'] + resource_data
		return RESPONSE_CODES['404']


	def load_document(self, request_path, document):
		try:
			with open(os.path.join(PATH + request_path, document),'rb') as fh:
				return fh.read()
		except FileNotFoundError:
			return None

	def run_script(self, request_path, document, arguments = None):
		# if not self.site_options and request_path != 'cgi-bin':
		# 	return None
		print(request_path, document)
		requested_resource = [os.path.join(PATH, request_path, document)]
		if arguments:
			requested_resource.extend(arguments)
		try:
			process = subprocess.Popen(requested_resource, stdout=subprocess.PIPE)
			resource_data, err = process.communicate()
			return resource_data
		except FileNotFoundError:
			return None
	
	def unquote(self, url):
  		return re.compile('%([0-9a-fA-F]{2})',re.M).sub(lambda m: chr(int(m.group(1),16)), url)

def main():
	webserver = WebServer('0.0.0.0', 3000)
	webserver.run_server()


if __name__ == '__main__':
	main()


