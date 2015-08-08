__author__ = 'micah'

import socket
#import os
import subprocess
import mimetypes
import re

class HTTPServer(object):

    def __init__(self, ipaddr, port):

        self.ipaddr = ipaddr
        self.port = port
        self.srv_options = {}
        self.parsed_header = None
        self.RESPONSE_CODES = {

            '200': b"HTTP/1.1 200 OK\r\nServer: My Little Server\r\n\
                Content-Type:text/html; charset=utf-8\r\n\n",
            '404': b"HTTP/1.1 404 Not Found\r\n\n404 Page Not Found",
            '301': b"HTTP/1.1 301 Redirect\r\nLocation: ",
            '501': b"HTTP/1.1 501 Not Implemented\r\n\nNot Implemented Yet",
            '400': b"HTTP/1.1 400 Bad Request\r\n\nUnable to Parse Header"
        }

    def load_site_options(self):
        try:
            with open('.serveroptions', 'r') as fh:
                for line in fh.readlines():
                    if line.strip() and line[0] is not '#':
                        line = line[:-1].split(';')
                        self.srv_options[line[0]] = line[1]
        except FileNotFoundError:
            print('Site options not found.')
            self.srv_options['webroot'] = 'sites'
            self.srv_options['df_idx'] = 'index.html'

    def run_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.ipaddr, self.port))
        sock.listen(socket.SOMAXCONN)
        self.load_site_options()
        print('Serving HTTP at {} port {}'.format(self.ipaddr, self.port))
        print('Site Index {}'.format('/'.join([self.srv_options['webroot'],
                                     self.srv_options['df_idx']])))
        while True:
            client, addr = sock.accept()
            data = client.recv(4096)
            print(data)
            if data:
                client.sendall(self.http_response(data))
            client.close()
        socket.close()

    def http_response(self, http_request):

        self.parsed_header = RequestParser(http_request.decode
                                          ('utf-8')).parse_header()
        if self.parsed_header:
            if not self.parsed_header['path'][1:]:
                self.parsed_header['path'] = self.srv_options['df_idx']
            if self.parsed_header['method'] == 'GET':
                page = ResourceObject('/'.join([self.srv_options['webroot'],
                                      self.parsed_header['path']])
                                      ).return_resource()
                if page:
                    return self.RESPONSE_CODES['200'] + page
                else:
                    return self.RESPONSE_CODES['404']
            if self.parsed_header['method'] == 'HEAD':
                return self.RESPONSE_CODES['200']
            return self.RESPONSE_CODES['501']
        return self.RESPONSE_CODES['400']


class RequestParser(object):

    def __init__(self, header):
        self.header = header

    def parse_header(self):
        try:
            parsed_header = {}
            self.header = self.header.split('\r\n')
            parsed_header['method'], parsed_header['path'], \
                parsed_header['protocol'] = self.header[0].split(' ')
            parsed_header['path'] = self.uri_decode(parsed_header['path'])
            if parsed_header['path'][1:] and parsed_header['path'][:-1] == '/':
                parsed_header['path'] += 'index.html'
            for item in self.header[1:]:
                if item:
                    item = item.split(':')
                    parsed_header[item[0]] = item[1]
            return parsed_header
        except (IndexError, KeyError):
            return None

    def uri_decode(self, url):
        url = re.compile('%([0-9a-fA-F]{2})', re.M)\
            .sub(lambda m: chr(int(m.group(1), 16)), url)
        url = url.replace('?', ' ')
        url = url.replace('+', ' ')
        return url


class ResourceObject(object):
    def __init__(self, requested_resource):
        self.requested_resource = requested_resource
        self.script_types = ('.py', '.py3')

    def return_resource(self):
        if self.requested_resource[self.requested_resource.rfind('.'):
                                   self.requested_resource.find('.')+3
                                   ] in self.script_types:
            self.run_script()
        else:
            self.load_document()
        return self.requested_resource

    def load_document(self):
        print('Serving: ' + self.requested_resource)
        try:
            with open(self.requested_resource, 'rb') as fh:
                self.requested_resource = fh.read()
        except FileNotFoundError:
            print(self.requested_resource + ' not found.')
            self.requested_resource = None

    def run_script(self):
        print('Running script at: ' + self.requested_resource)
        try:
            process = subprocess.Popen(self.requested_resource.split(' ', 1),
                                       stdout=subprocess.PIPE)
            resource_data, err = process.communicate()
            self.requested_resource = resource_data
        except FileNotFoundError:
            print(self.requested_resource + ' not found.')
            self.requested_resource = None


def main():
    webserver = HTTPServer('0.0.0.0', 3000)
    webserver.run_server()


if __name__ == '__main__':
    main()
