#!/usr/bin/env python3
#
# Copyright (C) 2016-2021 Savoir-faire Linux Inc.
#
# Author: Alexandre Viau <alexandre.viau@savoirfairelinux.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Creates packaging targets for a distribution and architecture.
# This helps reduce the length of the top Makefile.
#

import argparse

template_header = """\
# -*- mode: makefile -*-
# This file was auto-generated by: scripts/make-packaging-target.py.
#
# We don't simply use jami-packaging-distro as the docker image name because
# we want to be able to build multiple versions of the same distro at the
# same time and it could result in race conditions on the machine as we would
# overwrite the docker image of other builds.
#
# This does not impact caching as the docker daemon does not care about the image
# names, just about the contents of the Dockerfile.
"""

target_template = """\
##
## Distro: %(distribution)s
##

PACKAGE_%(distribution)s_DOCKER_IMAGE_NAME:=jami-packaging-%(distribution)s$(RING_PACKAGING_IMAGE_SUFFIX)
PACKAGE_%(distribution)s_DOCKER_IMAGE_FILE:=.docker-image-$(PACKAGE_%(distribution)s_DOCKER_IMAGE_NAME)

PACKAGE_%(distribution)s_DOCKER_RUN_COMMAND = docker run \\
    --rm \\
    -e RELEASE_VERSION=$(RELEASE_VERSION) \\
    -e RELEASE_TARBALL_FILENAME=$(RELEASE_TARBALL_FILENAME) \\
    -e DEBIAN_VERSION=%(version)s \\
    -e DEBIAN_QT_VERSION=%(version_qt)s \\
    -e CURRENT_UID=$(CURRENT_UID) \\
    -e CURRENT_GID=$(CURRENT_GID) \\
    -e DISTRIBUTION=%(distribution)s \\
    -v $(CURDIR)/$(RELEASE_TARBALL_FILENAME):/src/$(RELEASE_TARBALL_FILENAME) \\
    -v $(CURDIR):/opt/ring-project-ro:ro \\
    -v $(CURDIR)/packages/%(distribution)s:/opt/output \\
    -v /opt/cache-packaging:/opt/cache-packaging \\
    -v /opt/ring-contrib:/opt/ring-contrib \\
    -t $(and $(IS_SHELL_INTERACTIVE),-i) %(options)s \\
    $(DOCKER_RUN_EXTRA_ARGS) \\
    $(PACKAGE_%(distribution)s_DOCKER_IMAGE_NAME)

$(PACKAGE_%(distribution)s_DOCKER_IMAGE_FILE): docker/Dockerfile_%(docker_image)s
	docker build \\
        -t $(PACKAGE_%(distribution)s_DOCKER_IMAGE_NAME) \\
        -f docker/Dockerfile_%(docker_image)s %(docker_build_args)s \\
        $(CURDIR)
	touch $(PACKAGE_%(distribution)s_DOCKER_IMAGE_FILE)

packages/%(distribution)s:
	mkdir -p packages/%(distribution)s

packages/%(distribution)s/%(output_file)s: $(RELEASE_TARBALL_FILENAME) packages/%(distribution)s $(PACKAGE_%(distribution)s_DOCKER_IMAGE_FILE)
	$(PACKAGE_%(distribution)s_DOCKER_RUN_COMMAND)
	touch packages/%(distribution)s/*

.PHONY: package-%(distribution)s
package-%(distribution)s: packages/%(distribution)s/%(output_file)s
PACKAGE-TARGETS += package-%(distribution)s

.PHONY: package-%(distribution)s-interactive
package-%(distribution)s-interactive: $(RELEASE_TARBALL_FILENAME) packages/%(distribution)s $(PACKAGE_%(distribution)s_DOCKER_IMAGE_FILE)
	$(PACKAGE_%(distribution)s_DOCKER_RUN_COMMAND) bash
"""


RPM_BASED_SYSTEMS_DOCKER_RUN_OPTIONS = (
    '--security-opt seccomp=./docker/profile-seccomp-fedora_28.json '
    '--privileged')

DPKG_BASED_SYSTEMS_DOCKER_RUN_OPTIONS = (
    '-e QT_JAMI_PREFIX=$(QT_JAMI_PREFIX) '
    '-e QT_MAJOR=$(QT_MAJOR) '
    '-e QT_MINOR=$(QT_MINOR) '
    '-e QT_PATCH=$(QT_PATCH) '
    '-e QT_TARBALL_CHECKSUM=$(QT_TARBALL_CHECKSUM) '
    '-e FORCE_REBUILD_QT=$(FORCE_REBUILD_QT) '
    '-v /opt/ring-contrib:/opt/ring-contrib '
    '--privileged '
    '--security-opt apparmor=docker-default ')


def generate_target(distribution, output_file, options='', docker_image='',
                    version='', version_qt='', docker_build_args=''):
    if (docker_image == ''):
        docker_image = distribution
    if (version == ''):
        version = "$(DEBIAN_VERSION)"
    if (version_qt == ''):
        version_qt = "$(DEBIAN_QT_VERSION)"
    return target_template % {
        "distribution": distribution,
        "docker_image": docker_image,
        "output_file": output_file,
        "options": options,
        "version": version,
        "version_qt": version_qt,
        "docker_build_args": docker_build_args,
    }


def run_generate(parsed_args):
    print(generate_target(parsed_args.distribution,
                          parsed_args.output_file,
                          parsed_args.options,
                          parsed_args.docker_image,
                          parsed_args.version,
                          parsed_args.version_qt))


def run_generate_all(parsed_args):
    targets = [
        # Debian
        {
            "distribution": "debian_10",
            "output_file": "$(DEBIAN_DSC_FILENAME)",
            "options": DPKG_BASED_SYSTEMS_DOCKER_RUN_OPTIONS,
        },
        {
            "distribution": "debian_11",
            "output_file": "$(DEBIAN_DSC_FILENAME)",
            "options": DPKG_BASED_SYSTEMS_DOCKER_RUN_OPTIONS,
        },
        {
            "distribution": "debian_testing",
            "output_file": "$(DEBIAN_DSC_FILENAME)",
            "options": DPKG_BASED_SYSTEMS_DOCKER_RUN_OPTIONS,
        },
        {
            "distribution": "debian_unstable",
            "output_file": "$(DEBIAN_DSC_FILENAME)",
            "options": DPKG_BASED_SYSTEMS_DOCKER_RUN_OPTIONS,
        },
        # Raspbian
        {
            "distribution": "raspbian_10_armhf",
            "output_file": "$(DEBIAN_DSC_FILENAME)",
            "options": "--privileged --security-opt apparmor=docker-default",
        },
        # Ubuntu
        {
            "distribution": "ubuntu_18.04",
            "output_file": "$(DEBIAN_DSC_FILENAME)",
            "options": DPKG_BASED_SYSTEMS_DOCKER_RUN_OPTIONS,
        },
        {
            "distribution": "ubuntu_20.04",
            "output_file": "$(DEBIAN_DSC_FILENAME)",
            "options": DPKG_BASED_SYSTEMS_DOCKER_RUN_OPTIONS,
        },
        {
            "distribution": "ubuntu_21.04",
            "output_file": "$(DEBIAN_DSC_FILENAME)",
            "options": DPKG_BASED_SYSTEMS_DOCKER_RUN_OPTIONS,
        },
        # Fedora
        {
            "distribution": "fedora_33",
            "output_file": ".packages-built",
            "options": RPM_BASED_SYSTEMS_DOCKER_RUN_OPTIONS
        },
        {
            "distribution": "fedora_34",
            "output_file": ".packages-built",
            "options": RPM_BASED_SYSTEMS_DOCKER_RUN_OPTIONS
        },
        # Disabled 2021/05/21 because it's broken.
        # {
        #     "distribution": "rhel_8",
        #     "output_file": ".packages-built",
        #     "options": RPM_BASED_SYSTEMS_DOCKER_RUN_OPTIONS,
        #     "docker_build_args": "--build-arg PASS=$${PASS}"
        # },
        # OpenSUSE
        {
            "distribution": "opensuse-leap_15.2",
            "output_file": ".packages-built",
            "options": RPM_BASED_SYSTEMS_DOCKER_RUN_OPTIONS
        },
        {
            "distribution": "opensuse-leap_15.3",
            "output_file": ".packages-built",
            "options": RPM_BASED_SYSTEMS_DOCKER_RUN_OPTIONS
        },
        {
            "distribution": "opensuse-tumbleweed",
            "output_file": ".packages-built",
            "options": RPM_BASED_SYSTEMS_DOCKER_RUN_OPTIONS
        },
        # Snap
        {
            "distribution": "snap",
            "output_file": ".packages-built",
            "options": "-e SNAP_PKG_NAME=$(or $(SNAP_PKG_NAME),jami)",
        },

    ]

    for target in targets:
        print(generate_target(**target))


def parse_args():
    ap = argparse.ArgumentParser(
        description="Packaging targets generation tool"
    )

    ga = ap.add_mutually_exclusive_group(required=True)

    # Action arguments
    ga.add_argument('--generate',
                    action='store_true',
                    help='Generate a single packaging target')
    ga.add_argument('--generate-all',
                    action='store_true',
                    help='Generates all packaging targets')

    # Parameters
    ap.add_argument('--distribution')
    ap.add_argument('--output_file')
    ap.add_argument('--options', default='')
    ap.add_argument('--docker_image', default='')
    ap.add_argument('--version', default='')
    ap.add_argument('--version_qt', default='')

    parsed_args = ap.parse_args()

    return parsed_args


def main():
    parsed_args = parse_args()

    print(template_header)
    if parsed_args.generate:
        run_generate(parsed_args)
    elif parsed_args.generate_all:
        run_generate_all(parsed_args)

if __name__ == "__main__":
    main()
