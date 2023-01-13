#!/usr/bin/env python3
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
import subprocess
import shutil
import sys
import os

def usage(cmd):
	print("Usage:")
	print("%s [-h] [-v level] [-a] [-d dist_dir | " % cmd)
	print("     -gd root_dir dist_dir] [-qt qt_plugin_dir]")
	print("     [-xl x_locale_dir] [-cl c_locale_dir] [-tar output_tarball]")
	print("     executable")
	print("")
	print("  -v  : verbose level")
	print("          level 0 = completely quiet")
	print("          level 1 = libraries only")
	print("          level 2 = print everything")
	print("  -a  : use the dist_dir for multiple packages; implied when")
	print("        -gd is specified")
	print("  -d  : Create a self contained package in the specified directory.")
	print("  -gd : Create a global distribution package in root_dir.")
	print("        Shell scripts will be created relative to this root to ")
	print("        represent executables, and binary dependecies will be placed")
	print("        in the dist_dir, which must be inside the root base tree.")
	print("  Common paths:")
	print("    qt - /usr/lib/x86_64-linux-gnu/qt5/plugins")
	print("    xl - /usr/share/X11/locale")
	print("    cl - /usr/share/locale")
	exit(0)

def isELF(path):
	f = open(path,"rb")
	hdr = f.read(4)
	f.close()
	if hdr == b'\x7fELF':
		return True
	else:
		return False

def main(argv):
	if "-h" in argv:
		usage(argv[0])
		
	if "-d" in argv and "-gd" in argv:
		usage(argv[0])

	try:
		idx = argv.index("-v")
	except:
		verbose_level = 2
	else:
		if len(argv) < idx+2:
			usage(argv[0])
		try:
			verbose_level = int(argv[idx+1])
		except ValueError:
			usage(argv[0])
		del argv[idx]
		del argv[idx]
		
	try:
		idx = argv.index("-a")
	except:
		append_mode = False
	else:
		append_mode = True
		del argv[idx]

	if "-gd" in argv:
		global_mode = True
		append_mode = True
		idx = argv.index("-gd")
		if len(argv) < idx+3:
			usage(argv[0])
		root_dir = os.path.abspath(argv[idx+1])
		dist_dir = os.path.abspath(argv[idx+2])
		dst_dist_dir = dist_dir[len(root_dir):]
		if dist_dir[:len(root_dir)] != root_dir:
			usage(argv[0])
		del argv[idx]
		del argv[idx]
		del argv[idx]
	else:
		global_mode = False
		try:
			idx = argv.index("-d")
		except:
			dist_dir = "."
		else:
			if len(argv) < idx+2:
				usage(argv[0])
			dist_dir = argv[idx+1]
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

	try:
		idx = argv.index("-tar")
	except:
		dst_tgz_path = None
	else:
		if len(argv) < idx+2:
			usage(argv[0])
		else:
			dst_tgz_path = os.path.abspath(argv[idx+1])
			del argv[idx]
			del argv[idx]
			
	if len(argv) < 2:
		usage(argv[0])

	#Determine Paths
	src_exec = argv[1]
	exec_name = os.path.basename(src_exec)
	if global_mode:
		subdist_name = ""
		dst_script_path = os.path.join(root_dir,os.path.abspath(src_exec)[1:])
	else:
		if append_mode:
			subdist_name = "dist"
		else:
			subdist_name = "%s_dist"%exec_name
		dst_script_path = os.path.join(dist_dir,exec_name)
	dst_bin_dir = os.path.join(dist_dir,subdist_name,"bin")
	dst_lib_dir = os.path.join(dist_dir,subdist_name,"lib")
	dst_qt_dir = os.path.join(dist_dir,subdist_name,"plugins")+"/"
	dst_xl_dir = os.path.join(dist_dir,subdist_name,"xlocale")+"/"
	dst_cl_dir = os.path.join(dist_dir,subdist_name,"clocale")+"/"
	
	#Keep track of files that have already been examined/copied
	old_files = {}
	new_files = []

	#Make directories
	if not os.path.exists(dst_bin_dir):
		os.makedirs(dst_bin_dir)
	if not os.path.exists(dst_lib_dir):
		os.makedirs(dst_lib_dir)
	if src_qt_plugin and not os.path.exists(dst_qt_dir):
		os.makedirs(dst_qt_dir)
	if src_xlocaledir and not os.path.exists(dst_xl_dir):
		os.makedirs(dst_xl_dir)
	if src_clocaledir and not os.path.exists(dst_cl_dir):
		os.makedirs(dst_cl_dir)
	
	#Determine the loader
	loader_path = None
	loader_file = None
	proc = subprocess.Popen(["/usr/bin/strings",src_exec],stdout=subprocess.PIPE)
	while True:
		line = proc.stdout.readline().decode()
		if not len(line):
			break 
		line = line.strip()
		idx1 = line.find("/ld")
		idx2 = line.find(".so")
		if idx1 != -1 and idx2 != -1:
			loader_path = line
			loader_file = os.path.basename(loader_path)
			if not os.path.exists(loader_path):
				loader_path = None
				loader_file = None
			break
	if loader_path == None:
		print("Unable to determine loader")
		return 1

	#Find all qt plugins (just to be safe) and prep directories
	if src_qt_plugin:
		for root,dirs,files in os.walk(src_qt_plugin):
			for f in files:
				dst_dir = root.replace(src_qt_plugin,dst_qt_dir)
				if not os.path.exists(dst_dir):
					os.makedirs(dst_dir)
				src = os.path.join(root,f)
				new_files.append([2,src,dst_dir])

	#Find all xlocale files (just to be safe) and prep directories
	if src_xlocaledir:
		for root,dirs,files in os.walk(src_xlocaledir):
			for f in files:
				dst_dir = root.replace(src_xlocaledir,dst_xl_dir)
				dst_path = os.path.join(dst_dir,f)
				if not os.path.exists(dst_dir):
					os.makedirs(dst_dir)
				src = os.path.join(root,f)
				new_files.append([2,src,dst_dir])

	#Find all clocale files (just to be safe) and prep directories
	if src_clocaledir:
		for root,dirs,files in os.walk(src_clocaledir):
			for f in files:
				dst_dir = root.replace(src_clocaledir,dst_cl_dir)
				if not os.path.exists(dst_dir):
					os.makedirs(dst_dir)
				src = os.path.join(root,f)
				new_files.append([2,src,dst_dir])


	#Copy executable and loader (set executable to be examined)
	new_files.append([1,src_exec,dst_bin_dir])
	new_files.append([1,loader_path,dst_lib_dir])

	#Process all of the new files:
	#  1) Copy them into place
	#  2) Check is see if they require libraries
	#  3) Add required libraries to the new files list
	#Process all required libraries and get everything copied to lib
	while len(new_files):
		verbose,target,dstdir = new_files[0]
		if target in old_files:
			del new_files[0]
			continue

		if verbose <= verbose_level:
			print("File: %s" % target)

		dstfile = os.path.join(dstdir,os.path.basename(target))
		if os.path.exists(dstfile):
			if not append_mode and verbose <= verbose_level:
				print("  (already present in package)")
		else:
			shutil.copy(target,dstdir)

		if isELF(target):
			proc = subprocess.Popen(["/usr/bin/ldd",target],stdout=subprocess.PIPE)
			proc.wait()
			while True:
				line = proc.stdout.readline().decode()
				if not len(line):
					break
				line = line.strip()
				items = line.split(" ")
				if items[1] == "=>" and len(items[2]):
					if " ".join(items[2:]).lower() == "not found":
						print("Unidentified library: %s" % items[0])
					else:
						new_target = items[2]
						if verbose <= verbose_level:
							print("  -> %s" % new_target)
						new_files.append([1,new_target,dst_lib_dir])
		del new_files[0]
		old_files[target] = None

	#Create the launcher script
	f = open(dst_script_path,"w")
	f.write("#!/bin/bash\n")
	if global_mode:
		f.write("export LD_LIBRARY_PATH=%s/lib:$LD_LIBRARY_PATH\n"%dst_dist_dir)
		if src_qt_plugin:
			f.write("export QT_PLUGIN_PATH=%s/plugins\n"%dst_dist_dir)
		if src_xlocaledir:
			f.write("export XLOCALEDIR=%s/xlocale\n"%dst_dist_dir)
		if src_clocaledir:
			f.write("export LOCPATH=%s/clocale\n"%dst_dist_dir)
		f.write("%s/lib/%s %s/bin/%s $@\n" % (dst_dist_dir,loader_file,dst_dist_dir,exec_name))
		f.close()
	else:
		f.write("DIR=$(dirname $0)\n")
		f.write("export LD_LIBRARY_PATH=$DIR/%s/lib\n"%subdist_name)
		if src_qt_plugin:
			f.write("export QT_PLUGIN_PATH=$DIR/%s/plugins\n"%subdist_name)
		if src_xlocaledir:
			f.write("export XLOCALEDIR=$DIR/%s/xlocale\n"%subdist_name)
		if src_clocaledir:
			f.write("export LOCPATH=$DIR/%s/clocale\n"%subdist_name)
		f.write("$DIR/%s/lib/%s $DIR/%s/bin/%s $@\n" % (subdist_name,loader_file,subdist_name,exec_name))
	f.close()

	subprocess.call(["chmod","777",dst_script_path])
		
	#Create tarball
	if dst_tgz_path:
		if verbose_level == 0:
			args = "-czf"
		if verbose_level >= 1:
			print("Creating tarball: %s" % dst_tgz_path)
		if verbose_level >= 2:
			args = "-czvf"
			
		wd = os.getcwd()
		if global_mode:
			os.chdir(root_dir)
		else:
			os.chdir(dist_dir)
		files = [x for x in os.listdir(".") if x not in [".",".."]]
		subprocess.call(["tar",args,dst_tgz_path]+files)
		os.chdir(wd)
	
	return 0

if __name__ == "__main__":
	sys.exit(main(sys.argv))

