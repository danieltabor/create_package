#!/usr/bin/python
## Copyright (c) 2022 Daniel Tabor
##
## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions
## are met:
## 1. Redistributions of source code must retain the above copyright
##    notice, this list of conditions and the following disclaimer.
## 2. Redistributions in binary form must reproduce the above copyright
##    notice, this list of conditions and the following disclaimer in the
##    documentation and/or other materials provided with the distribution.
##
## THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS "AS IS" AND
## ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
## IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
## ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
## FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
## OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
## LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
## OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
## SUCH DAMAGE.
##
import sys
import os
import shutil
import create_package

exec_paths   = {}
data_paths   = {}
ignore_paths = {}

def usage(cmd):
	print "Usage:"
	print "%s [-h] [-c config_dir] src_dir [src_dir ...]" % cmd
	sys.exit(1)

def read_config(config_dir):
	global exec_paths
	global data_paths
	global ignore_paths
	
	for path, config_dict in [["HARVEST_EXEC",exec_paths],
														["HARVEST_DATA",data_paths],
														["HARVEST_IGNORE",ignore_paths]]:
		path = os.path.join(config_dir,path)
		if not os.path.exists(path):
			continue
		fp = open(path,"rb")
		while True:
			line = fp.readline()
			if not len(line):
				break
			line = line.strip()
			if not len(line) or line[0] == "#":
				continue
			config_dict[line] = None
		fp.close()

def write_config(config_dir):
	global exec_paths
	global data_paths
	for path, config_dict in [["HARVEST_EXEC",exec_paths],
														["HARVEST_DATA",data_paths]]:
		print "  %s: %d total files" % (path,len(config_dict))
		files = config_dict.keys()
		files.sort()
		fp = open(os.path.join(config_dir,path),"wb")
		for f in files:
			fp.write("%s\n" % f)
		fp.close()

def config_add(config_dict, path):
	global ignore_paths
	apath = os.path.abspath(path)
	if apath in config_dict:
		#Specific path is already configured
		return
	
	parts = apath.split("/")[1:]
	for i in xrange(len(parts)):
		test_path = "/".join(parts)
		if test_path in ignore_paths:
			#Configured to ignore this entire directory tree
			return
		elif test_path in config_dict:
			#Already configured to include this entire directory tree 
			return
	
	#No reason found to not include this file
	config_dict[apath] = None

def isELF(path):
	f = open(path,"rb")
	hdr = f.read(4)
	f.close()
	if hdr == "\x7fELF":
		return True
	else:
		return False

def main(argv):
	global exec_paths
	global data_paths

	if "-h" in argv:
		usage(argv[0])

	try:
		idx = sys.argv.index("-c")
	except:
		config_dir = "."
	else:
		if len(sys.argv) < idx+2:
			usage()
		else:
			config_dir = sys.argv[idx+1]
			if not os.path.isdir(config_dir):
				usage()
			del sys.argv[idx]
			del sys.argv[idx]

	try:
		idx = argv.index("-qt")
	except:
		src_qt_plugin = None
	else:
		if len(argv) < idx+2:
			usage(argv[0])
		else:
			src_qt_plugin = argv[idx+1]
			del argv[idx]
			del argv[idx]

	if len(argv) < 2:
		usage(argv[0])

	src_dirs = sys.argv[1:]

	#Read in the existing configuration
	read_config(config_dir)

	for src_dir in src_dirs:
		for root,dirs,files in os.walk(src_dir):
			for d in dirs:
				absfile = os.path.abspath(os.path.join(root,d))
				config_add(data_paths,absfile)
			for f in files:
				absfile = os.path.abspath(os.path.join(root,f))
				if os.path.islink(abspath):
					config_add(data_paths,absfile)
				else:
					try:
						if isELF(absfile):
							config_add(exec_paths,absfile)
						else:
							config_add(data_paths,absfile)
					except IOError:
						continue
	write_config(config_dir)

if __name__ == "__main__":
	main(sys.argv)

