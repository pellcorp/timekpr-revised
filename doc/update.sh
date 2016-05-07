#!/bin/sh
set -e
RST2MAN="/usr/share/docutils/scripts/python2/rst2man"

if [ -x "${RST2MAN}" ]; then
  echo "${0}: updating documentation..."
  ${RST2MAN} "doc/timekpr.rst" >"doc/timekpr.8"
  ${RST2MAN} "doc/timekpr.conf.rst" >"doc/timekpr.conf.5"
  ${RST2MAN} "doc/timekpr-client.rst" >"doc/timekpr-client.8"
  ${RST2MAN} "doc/timekpr-gui.rst" >"doc/timekpr-gui.8"
  ${RST2MAN} "doc/timekpr-gui3.rst" >"doc/timekpr-gui3.8"
  ${RST2MAN} "doc/users.timekpr.rst" >"doc/users.timekpr.8"
else
  echo "${0}: warning: 'rst2man' not found at '"${RST2MAN}"', documentation NOT updated!"
fi
