#!/usr/bin/env python
# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
#
# Copyright (c) 2015, Intel Corporation.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# AUTHORS
# Ed Bartosh <ed.bartosh@linux.intel.com>

"""Test cases for wic."""

import os

from glob import glob
from shutil import rmtree

from oeqa.selftest.base import oeSelfTest
from oeqa.utils.commands import runCmd, bitbake, get_bb_var, runqemu
from oeqa.utils.decorators import testcase


class Wic(oeSelfTest):
    """Wic test class."""

    resultdir = "/var/tmp/wic/build/"
    image_is_ready = False

    OE_IMAGE = "core-image-minimal"

    def setUpLocal(self):
        """This code is executed before each test method."""
        targetarch = get_bb_var('TARGET_ARCH', 'core-image-minimal')
        if 'x86' in targetarch:
            self.write_config('IMAGE_FSTYPES += " hddimg"\n'
                              'MACHINE_FEATURES_append = " efi"\n')

        # Do this here instead of in setUpClass as the base setUp does some
        # clean up which can result in the native tools built earlier in
        # setUpClass being unavailable.
        if not Wic.image_is_ready:
            tools = 'parted-native gptfdisk-native ' \
                    'dosfstools-native mtools-native bmap-tools-native'
            if 'x86' in targetarch:
                tools += 'syslinux syslinux-native'
            bitbake(tools)

            bitbake(self.OE_IMAGE)
            Wic.image_is_ready = True

        rmtree(self.resultdir, ignore_errors=True)

    @testcase(1208)
    def test_help(self):
        """Test wic --help"""
        self.assertEqual(0, runCmd('wic --help').status)

    @testcase(1209)
    def test_createhelp(self):
        """Test wic create --help"""
        self.assertEqual(0, runCmd('wic create --help').status)

    @testcase(1210)
    def test_listhelp(self):
        """Test wic list --help"""
        self.assertEqual(0, runCmd('wic list --help').status)

    @testcase(1211)
    def test_build_image_name(self):
        """Test wic create directdisk --image-name core-image-minimal"""
        self.assertEqual(0, runCmd("wic create directdisk "
                                   "--image-name %s" % self.OE_IMAGE).status)
        self.assertEqual(1, len(glob(self.resultdir + "directdisk-*.direct")))

    @testcase(1212)
    def test_build_artifacts(self):
        """Test wic create directdisk providing all artifacts."""
        bbvars = dict((var.lower(), get_bb_var(var, self.OE_IMAGE)) \
                        for var in ('STAGING_DATADIR', 'DEPLOY_DIR_IMAGE',
                                    'STAGING_DIR_NATIVE', 'IMAGE_ROOTFS'))
        status = runCmd("wic create directdisk "
                        "-b %(staging_datadir)s "
                        "-k %(deploy_dir_image)s "
                        "-n %(staging_dir_native)s "
                        "-r %(image_rootfs)s" % bbvars).status
        self.assertEqual(0, status)
        self.assertEqual(1, len(glob(self.resultdir + "directdisk-*.direct")))

    @testcase(1157)
    def test_gpt_image(self):
        """Test creation of core-image-minimal with gpt table and UUID boot"""
        self.assertEqual(0, runCmd("wic create directdisk-gpt "
                                   "--image-name %s" % self.OE_IMAGE).status)
        self.assertEqual(1, len(glob(self.resultdir + "directdisk-*.direct")))

    @testcase(1213)
    def test_unsupported_subcommand(self):
        """Test unsupported subcommand"""
        self.assertEqual(1, runCmd('wic unsupported',
                                   ignore_status=True).status)

    @testcase(1214)
    def test_no_command(self):
        """Test wic without command"""
        self.assertEqual(1, runCmd('wic', ignore_status=True).status)

    @testcase(1215)
    def test_help_overview(self):
        """Test wic help overview"""
        self.assertEqual(0, runCmd('wic help overview').status)

    @testcase(1216)
    def test_help_plugins(self):
        """Test wic help plugins"""
        self.assertEqual(0, runCmd('wic help plugins').status)

    @testcase(1217)
    def test_help_kickstart(self):
        """Test wic help kickstart"""
        self.assertEqual(0, runCmd('wic help kickstart').status)

    @testcase(1264)
    def test_compress_gzip(self):
        """Test compressing an image with gzip"""
        self.assertEqual(0, runCmd("wic create directdisk "
                                   "--image-name %s "
                                   "-c gzip" % self.OE_IMAGE).status)
        self.assertEqual(1, len(glob(self.resultdir + \
                                         "directdisk-*.direct.gz")))

    @testcase(1265)
    def test_compress_bzip2(self):
        """Test compressing an image with bzip2"""
        self.assertEqual(0, runCmd("wic create directdisk "
                                   "--image-name %s "
                                   "-c bzip2" % self.OE_IMAGE).status)
        self.assertEqual(1, len(glob(self.resultdir + \
                                         "directdisk-*.direct.bz2")))

    @testcase(1266)
    def test_compress_xz(self):
        """Test compressing an image with xz"""
        self.assertEqual(0, runCmd("wic create directdisk "
                                   "--image-name %s "
                                   "-c xz" % self.OE_IMAGE).status)
        self.assertEqual(1, len(glob(self.resultdir + \
                                         "directdisk-*.direct.xz")))

    @testcase(1267)
    def test_wrong_compressor(self):
        """Test how wic breaks if wrong compressor is provided"""
        self.assertEqual(2, runCmd("wic create directdisk "
                                   "--image-name %s "
                                   "-c wrong" % self.OE_IMAGE,
                                   ignore_status=True).status)

    @testcase(1268)
    def test_rootfs_indirect_recipes(self):
        """Test usage of rootfs plugin with rootfs recipes"""
        wks = "directdisk-multi-rootfs"
        wic_cmd_vars = {
            'wks': wks,
            'image': self.OE_IMAGE,
        }
        self.assertEqual(0, runCmd("wic create %(wks)s "
                                   "--image-name %(image)s "
                                   "--rootfs rootfs1=%(image)s "
                                   "--rootfs rootfs2=%(image)s" \
                                   % wic_cmd_vars).status)
        self.assertEqual(1, len(glob(self.resultdir + "%s*.direct" % wks)))

    @testcase(1269)
    def test_rootfs_artifacts(self):
        """Test usage of rootfs plugin with rootfs paths"""
        bbvars = dict((var.lower(), get_bb_var(var, self.OE_IMAGE)) \
                        for var in ('STAGING_DATADIR', 'DEPLOY_DIR_IMAGE',
                                    'STAGING_DIR_NATIVE', 'IMAGE_ROOTFS'))
        bbvars['wks'] = "directdisk-multi-rootfs"
        status = runCmd("wic create %(wks)s "
                        "-b %(staging_datadir)s "
                        "-k %(deploy_dir_image)s "
                        "-n %(staging_dir_native)s "
                        "--rootfs-dir rootfs1=%(image_rootfs)s "
                        "--rootfs-dir rootfs2=%(image_rootfs)s" \
                        % bbvars).status
        self.assertEqual(0, status)
        self.assertEqual(1, len(glob(self.resultdir + \
                                     "%(wks)s-*.direct" % bbvars)))

    @testcase(1346)
    def test_iso_image(self):
        """Test creation of hybrid iso image with legacy and EFI boot"""
        self.assertEqual(0, runCmd("wic create mkhybridiso "
                                   "--image-name %s" % self.OE_IMAGE).status)
        self.assertEqual(1, len(glob(self.resultdir + "HYBRID_ISO_IMG-*.direct")))
        self.assertEqual(1, len(glob(self.resultdir + "HYBRID_ISO_IMG-*.iso")))

    @testcase(1347)
    def test_image_env(self):
        """Test generation of <image>.env files."""
        self.assertEqual(0, bitbake('%s -c do_rootfs_wicenv' % self.OE_IMAGE).status)
        stdir = get_bb_var('STAGING_DIR_TARGET', self.OE_IMAGE)
        imgdatadir = os.path.join(stdir, 'imgdata')

        basename = get_bb_var('IMAGE_BASENAME', self.OE_IMAGE)
        self.assertEqual(basename, self.OE_IMAGE)
        path = os.path.join(imgdatadir, basename) + '.env'
        self.assertTrue(os.path.isfile(path))

        wicvars = set(get_bb_var('WICVARS', self.OE_IMAGE).split())
        # filter out optional variables
        wicvars = wicvars.difference(('HDDDIR', 'IMAGE_BOOT_FILES',
                                      'INITRD', 'ISODIR'))
        with open(path) as envfile:
            content = dict(line.split("=", 1) for line in envfile)
            # test if variables used by wic present in the .env file
            for var in wicvars:
                self.assertTrue(var in content, "%s is not in .env file" % var)
                self.assertTrue(content[var])

    @testcase(1351)
    def test_wic_image_type(self):
        """Test building wic images by bitbake"""
        self.assertEqual(0, bitbake('wic-image-minimal').status)

        deploy_dir = get_bb_var('DEPLOY_DIR_IMAGE')
        machine = get_bb_var('MACHINE')
        prefix = os.path.join(deploy_dir, 'wic-image-minimal-%s.' % machine)
        # check if we have result image and manifests symlinks
        # pointing to existing files
        for suffix in ('wic', 'manifest'):
            path = prefix + suffix
            self.assertTrue(os.path.islink(path))
            self.assertTrue(os.path.isfile(os.path.realpath(path)))

    @testcase(1348)
    def test_qemux86_directdisk(self):
        """Test creation of qemux-86-directdisk image"""
        image = "qemux86-directdisk"
        wic_cmd_vars = {
            'wks': image,
            'image': self.OE_IMAGE,
        }
        self.assertEqual(0, runCmd("wic create %(wks)s -e %(image)s" \
                                   % wic_cmd_vars).status)
        self.assertEqual(1, len(glob(self.resultdir + "%s-*direct" % image)))

    @testcase(1349)
    def test_mkgummidisk(self):
        """Test creation of mkgummidisk image"""
        image = "mkgummidisk"
        wic_cmd_vars = {
            'wks': image,
            'image': self.OE_IMAGE,
        }
        self.assertEqual(0, runCmd("wic create %(wks)s -e %(image)s" \
                                   % wic_cmd_vars).status)
        self.assertEqual(1, len(glob(self.resultdir + "%s-*direct" % image)))

    @testcase(1350)
    def test_mkefidisk(self):
        """Test creation of mkefidisk image"""
        image = "mkefidisk"
        wic_cmd_vars = {
            'wks': image,
            'image': self.OE_IMAGE,
        }
        self.assertEqual(0, runCmd("wic create %(wks)s -e %(image)s" \
                                   % wic_cmd_vars).status)
        self.assertEqual(1, len(glob(self.resultdir + "%s-*direct" % image)))

    @testcase(1385)
    def test_directdisk_bootloader_config(self):
        """Test creation of directdisk-bootloader-config image"""
        image = "directdisk-bootloader-config"
        wic_cmd_vars = {
            'wks': image,
            'image': self.OE_IMAGE,
        }
        self.assertEqual(0, runCmd("wic create %(wks)s -e %(image)s" \
                                   % wic_cmd_vars).status)
        self.assertEqual(1, len(glob(self.resultdir + "%s-*direct" % image)))

    @testcase(1422)
    def test_qemu(self):
        """Test wic-image-minimal under qemu"""
        self.assertEqual(0, bitbake('wic-image-minimal').status)

        with runqemu('wic-image-minimal', ssh=False) as qemu:
            command = "mount |grep '^/dev/' | cut -f1,3 -d ' '"
            status, output = qemu.run_serial(command)
            self.assertEqual(1, status, 'Failed to run command "%s": %s' % (command, output))
            self.assertEqual(output, '/dev/root /\r\n/dev/vda3 /mnt')

    def test_bmap(self):
        """Test generation of .bmap file"""
        image = "directdisk"
        wic_cmd_vars = {
            'wks': image,
            'image': self.OE_IMAGE,
        }
        status = runCmd("wic create %(wks)s -e %(image)s --bmap" \
                        % wic_cmd_vars).status
        self.assertEqual(0, status)
        self.assertEqual(1, len(glob(self.resultdir + "%s-*direct" % image)))
        self.assertEqual(1, len(glob(self.resultdir + "%s-*direct.bmap" % image)))

    def test_systemd_bootdisk(self):
        """Test creation of systemd-bootdisk image"""
        image = "systemd-bootdisk"
        wic_cmd_vars = {
            'wks': image,
            'image': self.OE_IMAGE,
        }
        self.assertEqual(0, runCmd("wic create %(wic)s -e %(image)s" \
                                   % wic_cmd_vars).status)
        self.assertEqual(1, len(glob(self.resultdir + "%s-*direct" % image)))

    def test_sdimage_bootpart(self):
        """Test creation of sdimage-bootpart image"""
        image = "sdimage-bootpart"
        kimgtype = get_bb_var('KERNEL_IMAGETYPE', self.OE_IMAGE)
        self.write_config('IMAGE_BOOT_FILES = "%s"\n' % kimgtype)
        wic_cmd_vars = {
            'wks': image,
            'image': self.OE_IMAGE,
        }
        self.assertEqual(0, runCmd("wic create %(wks)s -e %(image)s" \
                                   % wic_cmd_vars).status)
        self.assertEqual(1, len(glob(self.resultdir + "%s-*direct" % image)))
