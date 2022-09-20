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
import subprocess
import select

exec_paths   = {}
data_paths   = {}
ignore_paths = {}

def usage(cmd):
	print "Usage:"
	print "%s [-h] [-s strace_path] [-c config_dir] exe_path [args...]" % cmd
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

def dequote(s):
	if s[0] == "\"":
		if s[-1] != "\"":
			raise ValueError,"Not quoted %s" % s
		return s[1:-1]
	elif s[0] == "'":
		if s[-1] != "'":
			raise ValueError,"Not quoted %s" % s
		return s[1:-1]
	else:
		raise ValueError,"Not quoted %s" % s

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

def main(argv):
	global exec_paths
	global data_paths
	
	if "-h" in argv:
		usage(argv[0])

	try:
		idx = argv.index("-s")
	except:
		strace_path = None
	else:
		if len(argv) < idx+2:
			usage(argv[0])
		else:
			strace_path = argv[idx+1]
			del argv[idx]
			del argv[idx]

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

	if len(argv) < 2:
		usage(argv[0])

	exe_path = argv[1]
	exe_args = argv[2:]
	
	#Determine strace_path
	if strace_path == None:
		path_dirs = os.getenv("PATH","/bin:/usr/bin:/usr/local/bin").split(":")
		script_path = os.path.dirname(argv[0])
		#Give preference to the statically linked executable included
		#with this script
		path_dirs = [script_path] + path_dirs
		for d in path_dirs:
			if os.path.exists(d) and "strace" in os.listdir(d):
				strace_path = os.path.join(d,"strace")
				break
		if strace_path == None:
			print "ERROR: strace not found, please include path"
			print ""
			usage(argv[0])

	#Read in the existing configuration
	read_config(config_dir)

	#Run the program and parse STDERR
	file_paths = {}
	proc = subprocess.Popen([strace_path,"-f",exe_path]+exe_args,stderr=subprocess.PIPE)
	output = {}
	output[proc.pid] = ""
	while True:
		rl, wl, xl = select.select([proc.stderr],[],[],0)
		if len(rl):
			line = proc.stderr.readline()
			
			if not len(line):
				#Reached EOF on stderr, process is done
				break
			
			#Ignore any PID declarations at the beginning of the line
			if "[pid" == line[:4]:
				e_idx = line.find("]")
				if e_idx < 0:
					continue
				line = line[e_idx+1:].strip()
			
			#Attempt to identify a syscall and result
			try:
				call, result = [x.strip() for x in line.strip().split("=")]
			except ValueError:
				#No identifyable call and result
				#continue
				#This is a HACK to get around unfinished syscalls without
				#having to track output from different processess and threads
				call = line
				result = None
			else:
				#Treat result at an integer
				try:
					if "0x" == result[:2]:
						result = int(result.split(" ")[0],16)
					else:
						result = int(result.split(" ")[0])
				except ValueError:
					#Can not determine result
					continue
			
			#Identify the syscall and arguments
			call = call.strip()
			s_idx = call.find("(")
			if s_idx < 0:
				#No syscall on line
				continue
			sysfunc = call[:s_idx]
			sysargs = []
			esc = []
			arg = []
			for i in xrange(s_idx+1,len(call)):
				if not len(esc):
					if "<unfinished" == call[i:i+11]:
						#This is a HACK to get around unfinished syscalls 
						#for which we really don't care about the result
						if len(arg):
							sysargs.append("".join(arg))
							arg = []
						break
					elif call[i] == ")":
						#End of syscall
						if len(arg):
							sysargs.append("".join(arg))
							arg = []
						break
					elif call[i] == ",":
						#End of argument
						sysargs.append("".join(arg))
						arg = []
						continue
				
				#Handled layers of escaped arguments
				if len(esc) and call[i] == esc[-1]:
					esc = esc[:-1]
				elif call[i] == "[":
					esc.append("]")
				elif call[i] == "(":
					esc.append(")")
				elif call[i] == "\"":
					esc.append("\"")
				elif call[i] == "\'":
					esc.append("\'")
					
				arg.append(call[i])
			
			if sysfunc == "access":
				try:
					data_path = dequote(sysargs[0])
				except ValueError:
					continue
				config_add(data_paths,data_path)
			
			if sysfunc == "open" or sysfunc == "openat":
				if len(sysargs) == 3:
					data_path = sysargs[1]
				else:
					data_path = sysargs[0]
				try:
					data_path = dequote(data_path)
				except ValueError:
					continue
				config_add(data_paths,data_path)

			if sysfunc == "execve":
				try:
					exec_path = dequote(sysargs[0])
				except ValueError:
					continue
				config_add(exec_paths,exec_path)
				
	print "Harvester writing configuration files..."
	write_config(config_dir)
	
	print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	print "!!                                   !!"
	print "!! Do not forget to examine and edit !!"
	print "!! the configuration files before    !!"
	print "!! creating a Harvester package.     !!"
	print "!!                                   !!"
	print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

if __name__ == "__main__":
	main(sys.argv)

