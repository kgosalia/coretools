"""Tests to make sure that 'iotile build' works."""

# This file is adapted from python code released by WellDone International
# under the terms of the LGPLv3.  WellDone International's contact information is
# info@welldone.org
# http://welldone.org
#
# Modifications to this file from the original created at WellDone International
# are copyright Arch Systems Inc.

import os.path
import os
import shutil
import subprocess
import sys
import pytest
import distutils.core
from distutils.spawn import find_executable
from iotile.core.dev.registry import ComponentRegistry
from iotile.core.utilities.intelhex import IntelHex
from iotile.core.exceptions import *



def copy_folder(local_name, tmpdir):
    """Copy a complete folder by name into a temporary directory."""
    path = os.path.join(os.path.dirname(__file__), local_name)
    if not os.path.isdir(path):
        raise ValueError("%s is not a directory" % local_name)

    outpath = str(tmpdir.join(local_name))
    shutil.copytree(path, outpath)

    return outpath


def test_iotiletool():
    """Make sure the iotile tool works."""
    err = subprocess.check_call(["iotile", "quit"])
    assert err == 0


def test_build_command():
    """Make sure iotile.build has been properly registered as a plugin."""

    reg = ComponentRegistry()
    plugs = reg.list_plugins()
    assert 'build' in plugs


def test_build(tmpdir):
    """Make sure we can build a blank component."""

    olddir = os.getcwd()
    builddir = copy_folder('blank_component', tmpdir)

    try:
        os.chdir(builddir)
        err = subprocess.check_call(["iotile", "build"])
        assert err == 0
    finally:
        os.chdir(olddir)


def test_build_nodepends(tmpdir):
    """Make sure we can build a component with no depends key."""

    olddir = os.getcwd()
    builddir = copy_folder('component_nodependskey', tmpdir)

    try:
        os.chdir(builddir)
        err = subprocess.check_call(["iotile", "build"])
        assert err == 0
    finally:
        os.chdir(olddir)


def test_build_wheel_exception(tmpdir):
    """Make sure we raise a compatibility issue with a wheel"""

    base_wheel_name = "iotile_support_lib_controller_3-3.7.2-{0}-none-any.whl"

    if sys.version_info[0] == 3:
        wheel_to_copy = 'build/deps/iotile_standard_library_lib_controller/python/' + base_wheel_name.format('py2')
    else:
        wheel_to_copy = 'build/deps/iotile_standard_library_lib_controller/python/' + base_wheel_name.format('py3')

    olddir = os.getcwd()
    builddir = copy_folder('component_dep_wheels', tmpdir)

    try:
        os.chdir(builddir)
        w = open(wheel_to_copy, 'w')
        w.write("this was a triumph")
        w.close()
        with pytest.raises(Exception):
            subprocess.check_call(["iotile", "build"])
    finally:
        os.chdir(olddir)
        shutil.rmtree(builddir)


def test_build_wheel_compatible(tmpdir):
    """Make sure we don't raise a compatibility issue with a wheel that is compatible"""

    base_wheel_name = "iotile_support_lib_controller_3-3.7.2-{0}-none-any.whl"

    if sys.version_info[0] == 3:
        wheel_to_copy = 'build/deps/iotile_standard_library_lib_controller/python/' + base_wheel_name.format('py3')
    else:
        wheel_to_copy = 'build/deps/iotile_standard_library_lib_controller/python/' + base_wheel_name.format('py2')

    olddir = os.getcwd()
    builddir = copy_folder('component_dep_wheels', tmpdir)

    try:
        os.chdir(builddir)
        w = open(wheel_to_copy, 'w')
        w.write("this was a triumph")
        w.close()
        err = subprocess.check_call(["iotile", "build"])
        assert err == 0
    finally:
        os.chdir(olddir)
        shutil.rmtree(builddir)


def test_build_wheel_universal_exception(tmpdir):
    """Make sure we flag that a dependency needs to be universal if it's not"""

    base_wheel_name = "iotile_support_lib_controller_3-3.7.2-py3-none-any.whl"

    wheel_to_copy = 'build/deps/iotile_standard_library_lib_controller/python/' + base_wheel_name

    olddir = os.getcwd()
    builddir = copy_folder('component_dep_wheels_universal', tmpdir)

    try:
        os.chdir(builddir)
        w = open(wheel_to_copy, 'w')
        w.write("this was a triumph")
        w.close()
        with pytest.raises(Exception):
            subprocess.check_call(["iotile", "build"])
    finally:
        os.chdir(olddir)
        shutil.rmtree(builddir)


def test_build_wheel_universal_valid(tmpdir):
    """Make sure we flag that a dependency needs to be universal if it's not"""

    base_wheel_name = "iotile_support_lib_controller_3-3.7.2-py2.py3-none-any.whl"

    wheel_to_copy = 'build/deps/iotile_standard_library_lib_controller/python/' + base_wheel_name

    olddir = os.getcwd()
    builddir = copy_folder('component_dep_wheels_universal', tmpdir)

    try:
        os.chdir(builddir)
        w = open(wheel_to_copy, 'w')
        w.write("this was a triumph")
        w.close()
        err = subprocess.check_call(["iotile", "build"])
        assert err == 0

    finally:
        os.chdir(olddir)
        shutil.rmtree(builddir)


def test_build_with_python_depends(tmpdir):
    """Make sure we can build a component with a python package dependency"""
    olddir = os.getcwd()
    builddir = copy_folder('component_pythondepends', tmpdir)

    try:
        os.chdir(builddir)
        err = subprocess.check_call(["iotile", "build"])
        assert err == 0
    finally:
        os.chdir(olddir)


def test_build_arm(tmpdir):
    """Make sure we can build a component with no depends key."""

    olddir = os.getcwd()
    builddir = copy_folder('arm_component', tmpdir)

    try:
        os.chdir(builddir)
        err = subprocess.check_call(["iotile", "build"])
        assert err == 0
    finally:
        os.chdir(olddir)


def test_build_python(tmpdir):
    """Make sure we can build a component with a full python distribution."""

    olddir = os.getcwd()
    builddir = copy_folder('python_component', tmpdir)

    try:
        os.chdir(builddir)
        err = subprocess.check_call(["iotile", "build"])
        assert err == 0
    finally:
        os.chdir(olddir)


def test_python_depend_specifiers(tmpdir):
    """Make sure we generate the appropriate depdendency specifiers.

    See https://github.com/iotile/coretools/issues/514

    Previously we generated version specifiers for python support packages that
    were too specific so it was difficult to get them all installed properly.
    """

    olddir = os.getcwd()
    builddir = copy_folder('component_dep_wheels', tmpdir)

    base_wheel_name = "iotile_support_lib_controller_3-3.7.2-py2.py3-none-any.whl"
    wheel_to_copy = 'build/deps/iotile_standard_library_lib_controller/python/' + base_wheel_name

    try:
        os.chdir(builddir)
        with open(wheel_to_copy, 'w') as outfile:
            outfile.write("this was a triumph")

        err = subprocess.call(["iotile", "build"])
        assert err == 0

        os.chdir(os.path.join('build', 'python'))
        setup = distutils.core.run_setup('setup.py', stop_after='init')

        assert setup.install_requires == ['iotile_support_lib_controller_3==3.*,>=3.7.2']
    finally:
        os.chdir(olddir)


def test_build_prerelease(tmpdir):
    """Make sure we can build a component with no depends key."""

    olddir = os.getcwd()
    builddir = copy_folder('prerelease_component', tmpdir)

    try:
        os.chdir(builddir)
        err = subprocess.check_call(["iotile", "build"])
        assert err == 0
    finally:
        os.chdir(olddir)


@pytest.mark.skipif(find_executable('qemu-system-gnuarmeclipse') is None, reason="qemu emulator not installed")
def test_unit_testing(tmpdir):
    """Make sure we can build and run unit tests."""

    olddir = os.getcwd()
    builddir = copy_folder('comp_with_tests', tmpdir)

    try:
        os.chdir(builddir)
        err = subprocess.check_call(["iotile", "build", "build/test"])
        assert err == 0
    finally:
        os.chdir(olddir)


def test_bootstrap_file(tmpdir):
    """Make sure we can create a bootstrap file"""
    olddir = os.getcwd()
    builddir = copy_folder('component_bootstrap', tmpdir)

    try:
        os.chdir(builddir)

        print(os.listdir(os.path.join('build', 'output', builddir)))

        hexdata = IntelHex(os.path.join('build', 'output', 'test1.hex'))
        assert hexdata.segments() == [(0x10001014, 0x10001018)]

        assert not os.path.isfile(os.path.join('build', 'output', 'test2.hex'))

        err = subprocess.check_call(["iotile", "build"])
        assert err == 0

        hexdata = IntelHex(os.path.join('build', 'output', 'test_final.hex'))
        hexdata_dup = IntelHex(os.path.join('build', 'output', 'test_final_dup.hex'))
        assert hexdata.segments() == hexdata_dup.segments()
    finally:
        os.chdir(olddir)
