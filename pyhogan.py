import re
import cgi
import sys
from json import dumps


def walk(tree):
    code = []

    for i in range(0, len(tree)):
        tag = tree[i]['tag']
        if tag == '#':
            code.append(section(
                tree[i]['nodes'], tree[i]['n'], chooseMethod(tree[i]['n']),
                tree[i]['i'], tree[i]['end'],
                tree[i]['otag']+" "+tree[i]['ctag']))
        elif tag == '^':
            code.append(invertedSection(tree[i]['nodes'], tree[i]['n'],
                                        chooseMethod(tree[i]['n'])))
        elif tag == '<' or tag == '>':
            code.append(partial(tree[i]))
        elif tag == '{' or tag == '&':
            code.append(tripleStache(tree[i]['n'], chooseMethod(tree[i]['n'])))
        elif tag is None and tree[i]['text'] == '\n':
            code.append(text_eof('"\\n"' +
                                 ('' if len(tree)-1 == i else ' + i')))
        elif tag == '_v':
            code.append(variable(tree[i]['n'], chooseMethod(tree[i]['n'])))
        elif tag is None:
            code.append(text(tree[i]['text']))

    return ''.join(code)

def chooseMethod(s):
    return 'd' if '.' in s else 'f'

def section(nodes, id, method, start, end, tags):
    return 'if(_.s(_.' + method + '(' + dumps(id) + ',c,p,1),' + \
           'c,p,0,' + str(start) + ',' + str(end+1) + ', "' + tags + '")){' + \
           'b += _.rs(c,p,' + \
           'function(c,p){ var b = "";' + \
           walk(nodes) + \
           'return b;});c.pop();}' + \
           'else{b += _.b; _.b = ""};'

def invertedSection(nodes, id, method):
    return 'if (!_.s(_.'+method+'('+dumps(id)+',c,p,1),c,p,1,0,0,"")){' +\
           walk(nodes) + '};'

def partial(tok):
    return 'b += _.rp(%s,c,p,"%s");'%(dumps(tok['n']),tok.get('indent',''))

def tripleStache(id, method):
    return 'b += (_.%s(%s,c,p,0));'%(method, dumps(id))


def variable(id, method):
    return 'b += (_.v(_.%s(%s,c,p,0)));'%(method, dumps(id))

def text_eof(id):
    return 'b += %s;'%id

def text(id):
    return 'b += %s;'%dumps(id)


class Compiler(object):

    rIsWhitespace = re.compile('\S')
    tagTypes = {'#': 1, '^': 2, '/': 3,  '!': 4, '>': 5,
                '<': 6, '=': 7, '_v': 8, '{': 9, '&': 10}

    def scan(self, text, delimiters=[]):
        def lineIsWhitespace(tokens):
            isAllWhitespace = True
            for j in range(lineStart, len(tokens)):
                isAllWhitespace = (
                    (tokens[j]['tag'] and
                     (self.tagTypes[tokens[j]['tag']] < self.tagTypes['_v']))
                    or
                    (not tokens[j]['tag'] and
                     (self.rIsWhitespace.match(tokens[j]['text']) is None)))
                if not isAllWhitespace:
                    return False

            return isAllWhitespace

        def filterLine(tokens, haveSeenTag, noNewLine=False):
            if (haveSeenTag and lineIsWhitespace(tokens)):
                j = lineStart
                l = len(tokens);
                while j < l:
                    if not tokens[j]['tag']:
                        next_token = tokens[j+1]
                        if next_token['tag'] == '>':
                            next_token['indent'] = str(tokens[j]['text'])

                        del tokens[j]

                        l = len(tokens)
                    else:
                        j += 1

            elif not noNewLine:
                tokens.append({'text':'\n', 'tag':None});

        def changeDelimiters(text, index):
            close = '=' + ctag
            closeIndex = text.index(close, index)
            delimiters = text[text.index('=', index) + 1:
                              closeIndex].strip().split(' ')

            return closeIndex + len(close)-1, delimiters[0], delimiters[1]

        if (delimiters):
            otag = delimiters[0];
            ctag = delimiters[1];

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

        i = -1

        while i < text_len-1:
            i += 1
            if state == IN_TEXT:
                if self.tagChange(otag, text, i):
                    i -= 1
                    if len(buf) > 0:
                        tokens.append({'text': buf, 'tag': None})
                        buf = ''

                    state = IN_TAG_TYPE
                else:
                    if (text[i] == '\n'):
                        if len(buf) > 0:
                            tokens.append({'text': buf, 'tag': None})
                            buf = ''

                        filterLine(tokens, seenTag)
                        lineStart = len(tokens)
                        seenTag = False
                    else:
                        buf += text[i]

            elif state == IN_TAG_TYPE:
                i += len(otag)-1;
                tag = self.tagTypes.get(text[i+1])
                tagType = text[i+1] if tag else '_v';
                if tagType == '=':
                    i, otag, ctag = changeDelimiters(text, i);
                    state = IN_TEXT;
                else:
                    if tagType == '{':
                        i += 1

                    state = IN_TAG

                seenTag = i;
            else:
                if self.tagChange(ctag, text, i):
                    tokens.append(
                        {'tag': tagType,
                         'n': buf.strip(' \t\n\r\f\v#&/^>'),
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
                            i += 1
                        else:
                            self.cleanTripleStache(tokens[-1])
                else:
                    buf += text[i]

        if len(buf) > 0:
            tokens.append({'text': buf, 'tag': None})
            buf = ''
        filterLine(tokens, seenTag, True)
        return tokens

    def cleanTripleStache(self, token):
        if token['n'][len(token['n'])-1:] == '}':
            token['n'] = token['n'][0: len(token['n']) - 1]

    def tagChange(self, tag, text, index):
        if text[index] != tag[0]:
            return False

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
                stack.append(token)
                token['nodes'] = self.buildTree(
                    tokens, token['tag'], stack, customTags)
                instructions.append(token)
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
        tree = self.parse(tokens, text)
        code = 'function(c,p,i){i=i || "";var b=i+"";var _=this;%s return b}'%\
               walk(tree)
        if hogan:
            return 'new Hogan.Template(%s,%s,Hogan)'%(code, dumps(text))
        else:
            return code


def compile(text, hogan=True, verbose=False):
    return Compiler().compile(text, hogan, verbose)


def main():
    f = sys.argv[1]
    print compile(open(f, 'rb').read())
