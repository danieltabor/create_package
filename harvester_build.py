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
	print "%s [-h] [-c config_dir] [-qt qt_plugin_dir]" % cmd
	print "     [-xl x_locale_dir] [-cl c_locale_dir]"
	print "     root_dir dist_dir"
	print ""
	print "This program utilizes create_package called with the -gd argument."
	print ""
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
	global ignore_paths
	
	if "-h" in argv:
		usage(argv[0])

	try:
		idx = argv.index("-c")
	except:
		config_dir = "."
	else:
		if len(argv) < idx+2:
			usage(argv[0])
		else:
			config_dir = argv[idx+1]
			if not os.path.isdir(config_dir):
				usage(argv[0])
			del argv[idx]
			del argv[idx]

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

	try:
		idx = argv.index("-xl")
	except:
		src_xlocaledir = None
	else:
		if len(argv) < idx+2:
			usage(argv[0])
		else:
			src_xlocaledir = argv[idx+1]
			del argv[idx]
			del argv[idx]

	try:
		idx = argv.index("-cl")
	except:
		src_clocaledir = None
	else:
		if len(argv) < idx+2:
			usage(argv[0])
		else:
			src_clocaledir = argv[idx+1]
			del argv[idx]
			del argv[idx]

	if len(argv) < 3:
		usage(argv[0])

	root_dir = argv[1]
	dist_dir = argv[2]

	cp_args = ["create_package","-v","0","-gd",root_dir,dist_dir]
	if src_qt_plugin != None:
		cp_args.append("-qt")
		cp_args.append(src_qt_plugin)
	if src_xlocaledir != None:
		cp_args.append("-xl")
		cp_args.append(src_xlocaledir)
	if src_clocaledir != None:
		cp_args.append("-cl")
		cp_args.append(src_clocaledir)

	#Read in the existing configuration
	read_config(config_dir)

	error_files = []

	#Copy over all of the configured data paths
	data_files = data_paths.keys()
	data_files.sort()
	for data_file in data_files:
		if data_file[0] != "/":
			error_files.append(data_file)
			print "ERROR: Data file path: %s is not absolute" % data_file
			continue
		print "Harvesting Data Path: %s" % data_file
		if os.path.islink(data_file):
			#Create a symlink
			linkto = os.readlink(data_file)
			dst_dir = os.path.join(root_dir,os.path.dirname(data_file)[1:])
			dst = os.path.join(dst_dir,os.path.basename(data_file))
			if not os.path.exists(dst):
				os.symlink(linkto,dst)
		elif not os.path.isdir(data_file):
			#Just copy over a single file
			if not os.path.exists(data_file):
				error_files.append(data_file)
				print "ERROR: %s does not exists" % data_file
				continue
			dst_dir = os.path.join(root_dir,os.path.dirname(data_file)[1:])
			dst = os.path.join(dst_dir,os.path.basename(data_file))
			if not os.path.exists(dst_dir):
				os.makedirs(dst_dir)
			if not os.path.exists(dst):
				shutil.copy(data_file,dst)
		else:
			#Copy over an entire subtree
			for root,dirs,files in os.walk(data_file):
				for d in dirs:
					dst_dir = os.path.join(root_dir,root[1:],d)
					if not os.path.exists(dst_dir):
						os.makedirs(dst_dir)
				for f in files:
					src = os.path.join(root,f)
					dst_dir = os.path.join(root_dir,root[1:])
					dst = os.path.join(dst_dir,f)
					if not os.path.exists(dst_dir):
						os.makedirs(dst_dir)
					if not os.path.exists(dst):
						shutil.copy(src,dst)

	#Create portable packages for each executable
	exec_files = exec_paths.keys()
	exec_files.sort()
	for i in xrange(len(exec_files)):
		exec_file = exec_files[i]
		if exec_file[0] != "/":
			error_files.append(data_file)
			print "ERROR: Exec file path: %s is not absolute" % exec_file
			continue
		if not os.path.exists(exec_file):
			error_files.append(data_file)
			print "ERROR: Exec file path: %s does not exist" % exec_file
			continue
		dst_dir = os.path.join(root_dir,os.path.dirname(exec_file)[1:])
		if not os.path.exists(dst_dir):
			os.makedirs(dst_dir)
		if isELF(exec_file):
			print "Harvesting Binary: %s" % exec_file
			if create_package.main(cp_args+[exec_file]):
				error_files.append(exec_file)
		else:
			print "Harvesting Script: %s" % exec_file
			shutil.copy(exec_file,dst_dir)

	if len(error_files):
		print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
		print "!!"
		print "!! Build failed for the following files:"
		for f in error_files:
			print "!! %s" % f
		print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

if __name__ == "__main__":
	main(sys.argv)

