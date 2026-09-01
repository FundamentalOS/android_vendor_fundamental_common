#!/usr/bin/env python3
# Copyright (C) 2012-2013, The CyanogenMod Project
#           (C) 2017-2018,2020-2021, The LineageOS Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import glob
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from xml.etree import ElementTree

# FundamentalOS defaults: forks live under the FundamentalOS org on the '16'
# branch (declared as the fundamentalos remote's revision in
# snippets/fundamentalos.xml). Roomservice falls back to these when a device or
# dependency does not pin its own remote/branch.
FUNDAMENTAL_ORG = 'FundamentalOS'
FUNDAMENTAL_REMOTE = 'fundamentalos'
FUNDAMENTAL_BRANCH = '16'

dryrun = os.getenv('ROOMSERVICE_DRYRUN') == 'true'
if dryrun:
    print('Dry run roomservice, no change will be made.')

product = sys.argv[1]

if len(sys.argv) > 2:
    depsonly = sys.argv[2]
else:
    depsonly = None

try:
    device = product[product.index('_') + 1 :]
except IndexError:
    device = product

if not depsonly:
    print(
        f'Device {device} not found. Attempting to retrieve device repository from '
        f'FundamentalOS Github (https://github.com/{FUNDAMENTAL_ORG}).'
    )

repositories = []

if not depsonly:
    # The LineageOS mirror is only used as a codename -> repo-name catalog
    # (FundamentalOS has no mirror); the actual clone below targets the
    # FundamentalOS org via get_default_or_fallback_revision/add_to_manifest.
    githubreq = urllib.request.Request(
        'https://raw.githubusercontent.com/LineageOS/mirror/main/default.xml'
    )
    try:
        result = ElementTree.fromstring(
            urllib.request.urlopen(githubreq, timeout=10).read().decode()
        )
    except urllib.error.URLError:
        print('Failed to fetch data from GitHub')
        sys.exit(1)
    except ValueError:
        print('Failed to parse return data from GitHub')
        sys.exit(1)
    for res in result.findall('.//project'):
        repositories.append(res.attrib['name'][10:])

local_manifests = r'.repo/local_manifests'
if not os.path.exists(local_manifests):
    os.makedirs(local_manifests)


def exists_in_tree(lm, path):
    for child in lm.getchildren():
        if child.attrib['path'] == path:
            return True
    return False


# in-place prettyprint formatter
def indent(elem, level=0):
    i = '\n' + level * '  '
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + '  '
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def get_manifest_path():
    """Find the current manifest path
    In old versions of repo this is at .repo/manifest.xml
    In new versions, .repo/manifest.xml includes an include
    to some arbitrary file in .repo/manifests"""

    m = ElementTree.parse('.repo/manifest.xml')
    try:
        m.findall('default')[0]
        return '.repo/manifest.xml'
    except IndexError:
        return f'.repo/manifests/{m.find("include").get("name")}'


def get_from_manifest_project_paths(manifest_path):
    m = ElementTree.parse(manifest_path)
    m = m.getroot()
    return [x.get('path') for x in m.findall('project')]


def get_default_revision():
    m = ElementTree.parse(get_manifest_path())
    d = m.findall('default')[0]
    r = d.get('revision')
    return r.replace('refs/heads/', '').replace('refs/tags/', '')


def get_from_manifest(devicename):
    for path in glob.glob('.repo/local_manifests/*.xml'):
        try:
            lm = ElementTree.parse(path)
            lm = lm.getroot()
        except Exception:
            lm = ElementTree.Element('manifest')

        for localpath in lm.findall('project'):
            if re.search(f'android_device_.*_{device}$', localpath.get('name')):
                return localpath.get('path')

    return None


def is_in_manifest(tag, attr, attr_value):
    for path in glob.glob('.repo/local_manifests/*.xml'):
        try:
            lm = ElementTree.parse(path)
            lm = lm.getroot()
        except Exception:
            lm = ElementTree.Element('manifest')

        for localpath in lm.findall(tag):
            if localpath.get(attr) == attr_value:
                return True

    # Search in main manifest, too
    try:
        lm = ElementTree.parse(get_manifest_path())
        lm = lm.getroot()
    except Exception:
        lm = ElementTree.Element('manifest')

    for localpath in lm.findall(tag):
        if localpath.get(attr) == attr_value:
            return True

    # ... and don't forget the FundamentalOS / lineage snippets
    for snippet in (
        '.repo/manifests/snippets/fundamentalos.xml',
        '.repo/manifests/snippets/lineage.xml',
    ):
        try:
            lm = ElementTree.parse(snippet)
            lm = lm.getroot()
        except Exception:
            lm = ElementTree.Element('manifest')

        for localpath in lm.findall(tag):
            if localpath.get(attr) == attr_value:
                return True

    return False


def add_to_manifest(dependencies):
    if dryrun:
        return

    try:
        lm = ElementTree.parse('.repo/local_manifests/roomservice.xml')
        lm = lm.getroot()
    except Exception:
        lm = ElementTree.Element('manifest')

    for dependency in dependencies:
        dependency_type = dependency.get('type', 'project')

        if dependency_type == 'kernel':
            include_name = (
                f'manifests/snippets/kernel-{dependency["version"]}.xml'
            )
            print(f'Checking if {include_name} is included')
            if is_in_manifest('include', 'name', include_name):
                print(f'{include_name} already included')
                continue

            include = ElementTree.Element(
                'include',
                attrib={
                    'name': include_name,
                },
            )
            print(f'Adding dependency include: {include_name}')
            lm.append(include)
        elif dependency_type == 'project':
            repo_name = dependency['repository']
            repo_target = dependency['target_path']
            repo_revision = dependency['branch']
            print(f'Checking if {repo_target} is fetched from {repo_name}')
            if is_in_manifest('project', 'path', repo_target):
                print(f'{repo_name} already fetched to {repo_target}')
                continue

            # Resolve the remote and project name. Default to the FundamentalOS
            # remote; an explicit "remote" in the dependency can override it.
            if repo_remote := dependency.get('remote', None):
                if repo_remote.startswith('aosp-'):
                    remote_name, project_name = repo_remote, repo_name
                elif repo_remote == 'github':
                    # Explicit upstream LineageOS dependency.
                    remote_name, project_name = 'github', f'LineageOS/{repo_name}'
                else:
                    # Custom remotes (e.g. fundamentalos) already carry the org
                    # in their fetch URL, so use the bare repository name.
                    remote_name, project_name = repo_remote, repo_name
            else:
                remote_name, project_name = FUNDAMENTAL_REMOTE, repo_name

            attrib = {
                'path': repo_target,
                'remote': remote_name,
                'name': project_name,
            }
            # Only pin a revision when it differs from what the remote already
            # defaults to, so the entry inherits it otherwise:
            #   aosp-*        -> the aosp remote's own tag (+ shallow clone)
            #   github        -> the manifest-wide default (lineage-23.2)
            #   fundamentalos -> the remote's revision="16" (see snippet)
            if remote_name.startswith('aosp-'):
                attrib['clone-depth'] = '1'
            elif remote_name == 'github':
                if repo_revision and repo_revision != get_default_revision():
                    attrib['revision'] = repo_revision
            else:
                if repo_revision and repo_revision != FUNDAMENTAL_BRANCH:
                    attrib['revision'] = repo_revision

            project = ElementTree.Element('project', attrib=attrib)
            print(
                f'Adding dependency: {project.attrib["name"]} -> {project.attrib["path"]}'
            )
            lm.append(project)
        else:
            print(f'Unsupported dependency type: {dependency_type}')
            sys.exit(1)

    indent(lm, 0)
    raw_xml = ElementTree.tostring(lm).decode()
    raw_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + raw_xml

    f = open('.repo/local_manifests/roomservice.xml', 'w')
    f.write(raw_xml)
    f.close()


def fetch_dependencies(repo_path):
    print(f'Looking for dependencies in {repo_path}')
    dependencies_path = repo_path + '/fundamental.dependencies'
    # Fall back to the legacy lineage.dependencies name for upstream repos
    # that haven't been rebranded (e.g. the shared zumapro/gs-common trees).
    if not os.path.exists(dependencies_path):
        dependencies_path = repo_path + '/lineage.dependencies'
    syncable_repos = []
    verify_repos = []

    if os.path.exists(dependencies_path):
        with open(dependencies_path, 'r') as dependencies_file:
            dependencies = json.load(dependencies_file)
        fetch_list = []

        for dependency in dependencies:
            dependency_type = dependency.get('type', 'project')

            if dependency_type == 'kernel':
                include_name = (
                    f'manifests/snippets/kernel-{dependency["version"]}.xml'
                )
                if not is_in_manifest('include', 'name', include_name):
                    fetch_list.append(dependency)
                    syncable_repos += get_from_manifest_project_paths(
                        f'.repo/{include_name}'
                    )
            elif dependency_type == 'project':
                if not is_in_manifest(
                    'project', 'path', dependency['target_path']
                ):
                    fetch_list.append(dependency)
                    syncable_repos.append(dependency['target_path'])
                    if 'branch' not in dependency:
                        remote = dependency.get('remote', FUNDAMENTAL_REMOTE)
                        if remote.startswith('aosp-'):
                            dependency['branch'] = None
                        elif remote == 'github':
                            # upstream LineageOS: manifest-wide default revision
                            dependency['branch'] = get_default_revision()
                        else:
                            # FundamentalOS / custom remote fork
                            dependency['branch'] = (
                                get_default_or_fallback_revision(
                                    dependency['repository']
                                )
                            )
                            if not dependency['branch']:
                                sys.exit(1)
                verify_repos.append(dependency['target_path'])

                if not os.path.isdir(dependency['target_path']):
                    syncable_repos.append(dependency['target_path'])
            else:
                print(f'Unsupported dependency type: {dependency_type}')
                sys.exit(1)

        if len(fetch_list) > 0:
            print('Adding dependencies to manifest')
            add_to_manifest(fetch_list)
    else:
        print(f'{repo_path} has no additional dependencies.')

    if len(syncable_repos) > 0:
        print('Syncing dependencies')
        if not dryrun:
            subprocess.run(['repo', 'sync', '--force-sync'] + syncable_repos)

    for deprepo in verify_repos:
        fetch_dependencies(deprepo)


def get_default_or_fallback_revision(repo_name):
    # FundamentalOS forks track the '16' branch (the fundamentalos remote's
    # revision), independent of the manifest-wide default which stays
    # lineage-23.2 for upstream projects.
    default_revision = FUNDAMENTAL_BRANCH
    print(f'Default revision: {default_revision}')
    print('Checking branch info')

    try:
        stdout = subprocess.run(
            [
                'git',
                'ls-remote',
                '-h',
                f'https://:@github.com/{FUNDAMENTAL_ORG}/' + repo_name,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.decode()
        branches = [x.split('refs/heads/')[-1] for x in stdout.splitlines()]
    except Exception:
        return ''

    if default_revision in branches:
        return default_revision

    if os.getenv('ROOMSERVICE_BRANCHES'):
        fallbacks = list(
            filter(bool, os.getenv('ROOMSERVICE_BRANCHES').split(' '))
        )
        for fallback in fallbacks:
            if fallback in branches:
                print(f'Using fallback branch: {fallback}')
                return fallback

    print(
        f'Default revision {default_revision} not found in {repo_name}. Bailing.'
    )
    print('Branches found:')
    for branch in branches:
        print(branch)
    print(
        'Use the ROOMSERVICE_BRANCHES environment variable to specify a list of fallback branches.'
    )
    return ''


if depsonly:
    repo_path = get_from_manifest(device)
    if repo_path:
        fetch_dependencies(repo_path)
    else:
        print('Trying dependencies-only mode on a non-existing device tree?')

    sys.exit()

else:
    for repo_name in repositories:
        if re.match(r'^android_device_[^_]*_' + device + '$', repo_name):
            print(f'Found repository: {repo_name}')

            manufacturer = repo_name.replace('android_device_', '').replace(
                '_' + device, ''
            )
            repo_path = f'device/{manufacturer}/{device}'
            revision = get_default_or_fallback_revision(repo_name)
            if revision == '':
                # Some devices have the same codename but shipped a long time ago and may not have
                # a current branch set up.
                # Continue looking up all repositories until a match is found or no repos are left
                # to check.
                continue

            device_repository = {
                'repository': repo_name,
                'target_path': repo_path,
                'branch': revision,
            }
            add_to_manifest([device_repository])

            print('Syncing repository to retrieve project.')
            subprocess.run(['repo', 'sync', '--force-sync', repo_path])
            print('Repository synced!')

            fetch_dependencies(repo_path)
            print('Done')
            sys.exit()

print(
    f'Repository for {device} not found in the FundamentalOS Github org. If this is in error, you may need to manually add it to your local_manifests/roomservice.xml.'
)
