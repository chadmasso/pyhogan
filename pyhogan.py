import re
import sys
import json
from pprint import pprint


def walk(tree):
    code = []

    for i in range(0, len(tree)):
        tag = tree[i]['tag']
        if tag == '#':
            code.append(section(
                    tree[i].nodes, tree[i].n, chooseMethod(tree[i].n),
                    tree[i].i, tree[i].end, tree[i].otag + " " + tree[i].ctag))
        elif tag == '^':
            code.append(invertedSection(tree[i].nodes, tree[i].n,
                                        chooseMethod(tree[i].n)))
        elif tag == '<' or tag == '>':
            code.append(partial(tree[i]))
        elif tag == '{' or tag == '&':
            code.append(tripleStache(tree[i]['n'], chooseMethod(tree[i]['n'])))
        elif tag == '\n':
            code.append(text('"\\n"' + ('' if len(tree)-1 == i else ' + i')))
        elif tag == '_v':
            code.append(variable(tree[i].n, chooseMethod(tree[i].n)))
        elif tag is None:
            code.append(text(tree[i]['text']))

    return ''.join(code)

def chooseMethod(s):
    return 'd' if '.' in s else 'f'

def section(nodes, id, method, start, end, tags):
    return 'if(_.s(_.' + method + '("' + esc(id) + '",c,p,1),' + \
           'c,p,0,' + start + ',' + end + ', "' + tags + '")){' + \
           'b += _.rs(c,p,' + \
           'function(c,p){ var b = "";' + \
           walk(nodes) + \
           'return b;});c.pop();}' + \
           'else{b += _.b; _.b = ""};'

def invertedSection(self, nodes, id, method):
    return 'if (!_.s(_.' + method + '("' + esc(id) + '",c,p,1),c,p,1,0,0,"")){' +\
           walk(nodes) +\
           '};'

def partial(tok):
    return 'b += _.rp('+json.dumps(tok['n'])+',c,p,"'+(tok['indent']or'')+'");';

def tripleStache(id, method):
    return 'b += (_.' + method + '(' + json.dumps(id) + ',c,p,0));';

def variable(id, method):
    return 'b += (_.v(_.'+method+'('+json.dumps(id)+',c,p,0)));';

def text(id):
    return 'b += ' + json.dumps(id) + ';';


class Compiler(object):

    rIsWhitespace = re.compile('\S')
    rQuot = '\"'
    rNewline =  '\n',
    rCr = '\r',
    rSlash = '\\',
    tagTypes = {'#': 1, '^': 2, '/': 3,  '!': 4, '>': 5,
                '<': 6, '=': 7, '_v': 8, '{': 9, '&': 10}

    def __init__(self, f):
        self.f = f

    def scan(self, text, delimiters=[]):

        def lineIsWhitespace():
            isAllWhitespace = True
            for j in range(lineStart, len(tokens)):
                try:
                    isAllWhitespace = (
                        (tokens[j]['tag'] and
                         (self.tagTypes[tokens[j]['tag']] < self.tagTypes['_v']))
                        or
                        (not tokens[j]['tag'] and 
                         (self.rIsWhitespace.match(tokens[j]['text']) is None)))
                except:
                    print '1=========='
                    pprint (tokens)
                    print '1----------'
                    pprint (tokens[j])
                    raise
                if not isAllWhitespace:
                    return False

            return isAllWhitespace

        def filterLine(buf, haveSeenTag, noNewLine=False):
            if len(buf) > 0:
                tokens.append({'text': buf, 'tag': None})
                buf = ''

            if (haveSeenTag and lineIsWhitespace()):
                l = len(tokens);
                for j in range(lineStart, l):
                    if not tokens[j]['tag']:
                        next_token = tokens[j+1]
                        if next_token['tag'] == '>':
                            next_token['indent'] = str(tokens[j]['text'])

                    # ?
                    tokens.splice(j, 1);

            elif not noNewLine:
                tokens.append({'text':'\n', 'tag':None});

            # seenTag, lineStart, buf
            return False, len(tokens), buf

        def changeDelimiters(self, text, index):
            close = '=' + ctag
            closeIndex = text.indexOf(close, index)
            delimiters = trim(
                text.substring(text.indexOf('=', index) + 1, closeIndex)
                ).split(' ')

            otag = delimiters[0]
            ctag = delimiters[1]

            return closeIndex + close.length - 1

        #if (delimiters):
        #    delimiters = delimiters.split(' ');
        #    otag = delimiters[0];
        #    ctag = delimiters[1];

        text_len = len(text)
        IN_TEXT = 0
        IN_TAG_TYPE = 1
        IN_TAG = 2
        state = IN_TEXT
        tagType = None
        tag = None
        buf = ''
        tokens = []
        seenTag = False
        i = 0
        lineStart = 0
        otag = '{{'
        ctag = '}}'

        i = 0
        
        while i < text_len:
            if text[i] == '\n':
                print i, text[i-1]
            if state == IN_TEXT:
                if self.tagChange(otag, text, i):
                    i -= 1
                    if len(buf) > 0:
                        tokens.append({'text': buf, 'tag': None})
                        buf = ''

                    state = IN_TAG_TYPE
                else:
                    if (text[i] == '\n'):
                        seenTag, lineStart, buf = filterLine(buf, seenTag)
                    else:
                        buf += text[i]

            elif state == IN_TAG_TYPE:
                i += len(otag)-1;
                tag = self.tagTypes.get(text[i])
                tagType = text[i] if tag else '_v';
                if tagType == '=':
                    i = changeDelimiters(text, i);
                    state = IN_TEXT;
                else:
                    #if (tag):
                    #    i += 1

                    state = IN_TAG

                seenTag = i;
            else:
                if self.tagChange(ctag, text, i):
                    print '1--', tagType
                    tokens.append(
                        {'tag': tagType, 
                         'n': buf.strip(),
                         'otag': otag, 
                         'ctag': ctag,
                         'i': seenTag - len(ctag) if tagType == '/' 
                                                  else i + len(otag)
                         })
                    buf = ''
                    i += len(ctag)-1
                    state = IN_TEXT
                    if tagType == '{':
                        if ctag == '}}':
                            #i += 1
                            pass
                        else:
                            cleanTripleStache(tokens[tokens.length - 1])
                else:
                    buf += text[i]

            i += 1;

        filterLine(buf, seenTag, True)
        return tokens

    def tagChange(self, tag, text, index):
        if text[index] != tag[0]:
            return False

        i = 1
        l = len(tag)
        for i in range(0, len(tag)):
            if text[index + i] != tag[i]:
                return False

        return True

    def buildTree(self, tokens, kind, stack, customTags):
        instructions = []
        opener = None
        token = None

        while len(tokens) > 0:
            token = tokens[0]
            del tokens[0]
            
            if (token['tag'] == '#' or token['tag'] == '^' 
                or self.isOpener(token, customTags)):
                stack.push(token);
                token.nodes = buildTree(tokens, token.tag, stack, customTags);
                instructions.push(token);
            elif token['tag'] == '/':
                if (len(stack) == 0):
                    raise Exception('Closing tag without opener: /'+token['n'])

                opener = stack.pop()
                if (token['n'] != opener['n'] and \
                        not self.isCloser(token['n'], opener['n'], customTags)):
                    raise Exception('Nesting error: '+
                                    opener['n']+' vs. '+token['n'])

                opener['end'] = token['i']
                return instructions
            else:
                instructions.append(token)

        if len(stack) > 0:
            raise Exception('missing closing tag: ' + stack.pop()['n'])

        return instructions;

    def isOpener(self, token, tags):
        for i in range(0, len(tags)):
            if tags[i]['o'] == token['n']:
                token['tag'] = '#';
                return True

    def isCloser(self, close, open, tags):
        for i in range(0, len(tags)):
            if (tags[i]['c'] == close and tags[i]['o'] == open):
                return True

    def parse(self, tokens, text, options={}):
        return self.buildTree(tokens, '', [], [])

    def compile(self, text, hogan=True, verbose=False):
        tokens = self.scan(text)
        if verbose:
            pprint (tokens)
        tree = self.parse(tokens, text)
        code = 'function(c,p,i){i=i || "";var b=i+"";var _ = this;%s return b}'%\
            walk(tree)
        if hogan:
            return 'new Hogan.Template(%s,"",Hogan)'%code
        else:
            return code


def compile(text, hogan=True, verbose=False):
    return Compiler(text).compile(text, hogan, verbose)


def main():
    f = sys.argv[1]
    print compile(open(f, 'rb').read())
