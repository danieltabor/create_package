# Create Package Tools

These scripts were made to solve the problem of moving a working Linux executable from the system it was built on to another Linux system.  If the vintages, distributions, and installed packages of these two systems are similar enough, this transition is as easy as copying the executable file.  However, this is not always the case.  So, these scripts can be used to determine the required support files (dynamic libraries, etc.) for a working executable.  They then copy the executable and required support files into a seperate distribution directory and create a script that modifies environmental variables to force the support files on the original, build, system to be used rather than the native files of the executing system.

These scripts are not perfect or comprehensive, but work reasonably well for general executables (including Qt based applications).

# Tool Descriptions

create_package.py
-----------------
This tool is used to create stand-alone distibutions for a single
executable, such that it can be portable between wildly different
Linux distributions.

Usage:
./create_package.py [-h] [-v level] [-a] [-d dist_dir | 
     -gd root_dir dist_dir] [-qt qt_plugin_dir]
     [-xl x_locale_dir] [-cl c_locale_dir] [-tar output_tarball]
     executable

  -v  : verbose level
          level 0 = completely quiet
          level 1 = libraries only
          level 2 = print everything
  -a  : use the dist_dir for multiple packages; implied when
        -gd is specified
  -d  : Create a self contained package in the specified directory.
  -gd : Create a global distribution package in root_dir.
        Shell scripts will be created relative to this root to 
        represent executables, and binary dependecies will be placed
        in the dist_dir, which must be inside the root base tree.
  Common paths:
    qt - /usr/lib/x86_64-linux-gnu/qt5/plugins
    xl - /usr/share/X11/locale
    cl - /usr/share/locale



harvester_config.py
-------------------
This tool takes a single executable and executes it.  It uses strace to record
every file that is subsequently excuted by the process or one of its 
descendants.  It also recordes every file opened by the process or one of its 
descendants.  It creates the configuration files HARVEST_EXEC and HARVEST_DATA,
which can later be used by the harvester_build.py tool.  Any file or directory
listed in HARVEST_IGNORE will be ignored.

Usage:
./harvester_config.py [-h] [-s strace_path] [-c config_dir] exe_path [args...]



harvester_stripmine.py
----------------------
This tool takes the root of a directory tree and walks through it attempting
to determine which files are executables and which are data.  It writes 
configurations files ( HARVEST_EXEC, HARVEST_DATA ) to be used later to build
large scale portable distribtuions.  Any files, or directory trees, listed in
HARVEST_IGNORE, are ignored during this process.

The HARVEST_EXEC and HARVEST_DATA files can be manually edited to improve the
output of harvester_config.py.  Also, repeated runs of the program will expand
on the any existing configuration files.

Usage:
./harvester_stripmine.py [-h] [-c config_dir] src_dir [src_dir ...]




harvester_build.py
------------------
This tools that the configuration files HARVEST_EXEC and HARVEST_DATA and
creates a distribution directory.  The tool create_package.py is used for
each of the executables, and all of the data files are copied into the
distribution directory.

Usage:
./harvester_build.py [-h] [-c config_dir] [-qt qt_plugin_dir]
     [-xl x_locale_dir] [-cl c_locale_dir]
     root_dir dist_dir

This program utilizes create_package called with the -gd argument.
