#!/usr/bin/env python
import argparse
from contextlib import closing
import httplib
import json
import logging
import os
import re
import subprocess
import sys
import urllib2
logger = logging.getLogger('irkit')

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--verbose', '-v', action='append_const', const=1)
	parser.add_argument('commands', nargs='+')
	args = parser.parse_args()
	logging.basicConfig()
	if args.verbose: logger.setLevel(level=logging.INFO if len(args.verbose) == 1 else logging.DEBUG)
	command = args.commands[0]
	if command == 'list':
		for name in IRKit.iter_names(sys.maxint):
			print(name)
		return
	settings_path = os.path.expanduser('~/.irkit/settings.json')
	settings = load_settings(settings_path)
	name = settings.get('name')
	if not name:
		name = first(IRKit.iter_names(1))
		settings['name'] = name
	irkit = IRKit(name)
	irkit.scope = settings.get('scope')
	if command == 'save':
		irkit.save(args.commands[1:])
	else:
		irkit.execute(args.commands)
	settings['scope'] = irkit.scope
	save_settings(settings, settings_path)

class IRKit(object):
	def __init__(self, name):
		self._data_dir = os.path.expanduser('~/.irkit')
		self._scope_dir = self._data_dir
		self.name = name

	@property
	def url_base(self):
		return 'http://' + self.name + '/'

	@staticmethod
	def iter_names(max=1):
		logger.info('Looking for IRKit...')
		p = subprocess.Popen(('dns-sd', '-B', '_irkit._tcp'), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		for line in iter(p.stdout.readline, b''):
			line = line.strip()
			logger.debug('dns-sd: %s', line)
			values = line.split()
			if len(values) < 5 or values[1] != 'Add':
				continue
			yield values[6]
			max -= 1
			if max <= 0:
				break
		p.kill()
		logger.debug('iter_names killed')

	@property
	def scope(self):
		if not self._scope_dir or self._scope_dir == self._data_dir:
			return ()
		relpath = os.path.relpath(self._scope_dir, self._data_dir)
		return relpath.split('/')

	@scope.setter
	def scope(self, scope):
		if not scope:
			self._scope_dir = self._data_dir
		else:
			self._scope_dir = os.path.join(self._data_dir, *scope)
		logger.info('scope=%s (%s)', self.scope, self._scope_dir)

	@property
	def scope_dirs(self):
		dir = self._scope_dir
		if not dir:
			yield self._data_dir
			return
		while True:
			yield dir
			if dir == self._data_dir:
				break
			dir = os.path.dirname(dir)

	def _set_scope_dir(self, dir):
		self._scope_dir = dir
		logger.info('scope=%s (%s)', self.scope, self._scope_dir)

	def execute(self, commands):
		for command in commands:
			mul_match = re.search(r'\*(\d+)$', command)
			if mul_match:
				command = command[0:mul_match.start(0)]
			logger.debug('Looking for "%s"', command)
			for dir in self.scope_dirs:
				logger.debug('Looking for "%s" in "%s"', command, dir)
				dir = os.path.join(dir, command)
				path = dir + '.ir'
				found = False
				if os.path.exists(path):
					if mul_match:
						for i in range(int(mul_match.group(1)) - 1):
							self.send(path)
					self.send(path)
					found = 1
				if os.path.isdir(dir):
					self._set_scope_dir(dir)
					break
				if found:
					break
			else:
				logger.error('Command "%s" not found', command)

	def send(self, path):
		url = self.url_base + 'messages'
		logger.info('Sending %s to %s', path, url)
		with open(path, 'r') as fp:
			data = fp.read()
		with closing(urllib2.urlopen(url, data=data)) as rs:
			pass

	def save(self, commands):
		url = self.url_base + 'messages'
		logger.debug('Requesting data from %s', url)
		try:
			with closing(urllib2.urlopen(url)) as rs:
				data = rs.read()
		except httplib.BadStatusLine:
			logger.error('No data received (BadStatusLine.)')
			return False
		if not data:
			logger.error('No data received.')
			return False
		logger.debug('Received: %s', data)
		path = os.path.join(self._data_dir, *commands[0:-1])
		if not os.path.isdir(path):
			os.makedirs(path)
		path = os.path.join(path, commands[-1]) + '.ir'
		with open(path, 'w') as fp:
			fp.write(data)
		logger.info('Saved to %s.', path)
		return True

def load_settings(path):
	if not os.path.exists(path):
		return {}
	with open(path, 'r') as fp:
		return json.load(fp)

def save_settings(settings, path):
	logger.debug('Saving settings to %s', path)
	dir = os.path.dirname(path)
	if not os.path.isdir(dir): os.makedirs(dir)
	with open(path, 'w') as fp:
		json.dump(settings, fp, indent=0, sort_keys=True)

def first(iterable, default=None):
	if iterable:
		for item in iterable:
			return item
	return default

if __name__ == '__main__':
	main()
