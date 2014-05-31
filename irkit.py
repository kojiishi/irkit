#!/usr/bin/env python
import argparse
from contextlib import closing
import httplib
import json
import logging
import os
import subprocess
import urllib2
logger = logging.getLogger('irkit')

class IRKit(object):
	def __init__(self, name):
		self.datadir = os.path.expanduser('~/.irkit')
		self.name = name

	@property
	def url_base(self):
		return 'http://' + self.name + '/'

	@staticmethod
	def iter_names(max=1):
		logger.info('Looking for IRKit...')
		p = subprocess.Popen(('dns-sd', '-B', '_irkit._tcp'), stdout=subprocess.PIPE)
		print p.stdout.readline()
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

	def execute(self, commands):
		path = os.path.join(self.datadir, *commands) + '.ir'
		with open(path, 'r') as fp:
			data = fp.read()
		url = self.url_base + 'messages'
		logger.debug('Sending %s to %s', path, url)
		with closing(urllib2.urlopen(url, data=data)) as rs:
			pass

	def save(self, commands):
		url = self.url_base + 'messages'
		logger.debug('Requesting data from %s', url)
		try:
			with closing(urllib2.urlopen(url)) as rs:
				data = rs.read()
		except httplib.BadStatusLine:
			logger.error('BadStatusLine')
			return False
		if not data:
			logger.error('No data received.')
			return False
		logger.debug('Received: %s', data)
		path = os.path.join(self.datadir, *commands[0:-1])
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

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--verbose', '-v', action='append_const', const=1)
	parser.add_argument('commands', nargs='+')
	args = parser.parse_args()
	logging.basicConfig()
	if args.verbose: logger.setLevel(level=logging.INFO if len(args.verbose) == 1 else logging.DEBUG)
	settings_path = os.path.expanduser('~/.irkit/settings.json')
	settings = load_settings(settings_path)
	name = settings.get('name')
	if not name:
		name = first(IRKit.iter_names(1))
		settings['name'] = name
	irkit = IRKit(name)
	if args.commands[0] == 'save':
		irkit.save(args.commands[1:])
	else:
		irkit.execute(args.commands)
	save_settings(settings, settings_path)

main()
