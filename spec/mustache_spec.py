import os
import sys
import json
import tempfile
import subprocess

SPEC = os.path.split(__file__)[0]
FILES = os.path.join(SPEC, '_files')
ROOT = os.path.join(SPEC, '..')

HOGAN = open(os.path.join(SPEC, 'hogan-1.0.5.common.js'), 'rb').read();

NODE_PATH = '/home/fafhrd/opt/bin/node'

sys.path.append(ROOT)

import pyhogan

def load_test(name):
  template = open(os.path.join(FILES, "%s.mustache"%name), 'rb').read()
  view = open(os.path.join(FILES, "%s.js"%name), 'rb').read()
  partial_file = os.path.join(FILES, "%s.partial"%name)
  partial = ''
  if os.path.isfile(partial_file):
    partial = open(partial_file, 'rb').read()

  expect = open(os.path.join(FILES, "%s.txt"%name), 'rb').read()
  return [template, view, partial, expect]

def run_js(js):
  fd, name = tempfile.mkstemp()
  runner_file = os.fdopen(fd, 'w+b')
  runner_file.write(js)
  runner_file.close()
  res = subprocess.check_output((NODE_PATH, name))
  runner_file.close()
  os.unlink(name)
  return res


JS = """%(hogan)s

try {
var TEMPLATE = %(tmpl)s;
%(view)s

var partial = {partial: %(partial)s};

console.log(TEMPLATE.render(%(name)s));
} catch (e) {
   console.log(e);
}
"""

print "Testing in V8 "

tests = sys.argv[1:]

for name in sorted(os.listdir(FILES)):
  if name.endswith('.mustache'):
    name = name[:-9]
    if tests and name not in tests:
      continue

    template, view, partial, expect = load_test(name)
    
    js = JS%{
      'name': name,
      'tmpl': pyhogan.compile(template, verbose=bool(tests)),
      'view': view,
      'partial': json.dumps(partial),
      'hogan': HOGAN
      }

    res = run_js(js).strip()
    print name, '...',
    if res == expect:
      print 'passed'
    else:
      print 'FAILED'

    if tests:
      print pyhogan.compile(template)
      print 'got: -------------------------'
      print res
      print 'expect: ----------------------'
      print expect
      print '=========================='
