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

def usage():
	print "Usage:"
	print "%s [-h] [-s strace_path] [-o log_output] exe_path" % sys.argv[0]
	sys.exit(1)

def main():
	if "-h" in sys.argv:
		usage()

	try:
		idx = sys.argv.index("-s")
	except:
		strace_path = None
	else:
		if len(sys.argv) < idx+2:
			usage()
		else:
			strace_path = sys.argv[idx+1]
			del sys.argv[idx]
			del sys.argv[idx]

	try:
		idx = sys.argv.index("-o")
	except:
		output_fp = sys.stdout
	else:
		if len(sys.argv) < idx+2:
			usage()
		else:
			output_fp = file(sys.argv[idx+1],"wb")
			del sys.argv[idx]


	if len(sys.argv) < 2:
		usage()

	exe_path = sys.argv[1]

	#Determine strace_path
	if strace_path == None:
		path_dirs = os.getenv("PATH","/bin:/usr/bin:/usr/local/bin").split(":")
		for d in path_dirs:
			if "strace" in os.listdir(d):
				strace_path = os.path.join(d,"strace")
				break
		if strace_path == None:
			print "ERROR: strace not found, please include path"
			print ""
			usage()


	#Run the program and parse STDERR
	file_paths = {}
	proc = subprocess.Popen([strace_path,exe_path],stderr=subprocess.PIPE)
	while True:
		rl, wl, xl = select.select([proc.stderr],[],[],0)
		if len(rl):
			line = proc.stderr.readline()
			if not len(line):
				#Reached EOF on stderr, process is done
				break
			if "open(" != line[:5] and "openat(" != line[:7]:
				continue
			c, r = [x.strip() for x in line.strip().split("=")]
			try:
				r = int(r)
			except ValueError:
				continue
			if r > 0:
				s_idx = c.index("(")
				e_idx = c.index(")")
				if s_idx >= 0 and e_idx >= 0:
					params = [x.strip() for x in c[s_idx+1:e_idx].split(",")]
					if len(params) == 3:
						path = params[1]
					else:
						path = params[0]
					if path[0] != "\"" or path[-1] != "\"":
						continue
					path = path[1:-1]
					if path not in file_paths:
						file_paths[path] = None
	
	#Write the output
	output_fp.write("#######################################\n")
	output_fp.write("##  Files used by %s\n" % exe_path)
	output_fp.write("#######################################\n")
	paths = file_paths.keys()
	paths.sort()
	for p in paths:
		output_fp.write("%s\n"%p)
	output_fp.write("\n")
	

if __name__ == "__main__":
	main()

