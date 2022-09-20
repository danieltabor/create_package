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

def usage(cmd):
	print "Usage:"
	print "%s [-h] [-v] root_dir output_tarball" % cmd
	print ""
	sys.exit(1)

def main(argv):
	if "-h" in argv:
		usage(argv[0])

	try:
		idx = argv.index("-v")
	except:
		verbose = False
	else:
		verbose = True
		del argv[idx]

	if len(argv) < 2:
		usage(argv[0])
	
	root_dir = os.path.abspath(argv[1])
	dst_tgz_path = os.path.abspath(argv[2])
	
	if verbose:
		args = "-czvf"
	else:
		args = "-czf"
	
	#Create tarball
	wd = os.getcwd()
	os.chdir(root_dir)
	files = [x for x in os.listdir(".") if x not in [".",".."]]
	subprocess.call(["tar",args,dst_tgz_path]+files)
	os.chdir(wd)

if __name__ == "__main__":
	main(sys.argv)

