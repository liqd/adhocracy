"""
Truncate given HTML to a certain number of target characters while preserving
the HTML structure and whole words.

Code is taken from https://raw.github.com/enkore/typeflow/ revision d4b2f35c14,

Original: https://raw.github.com/eentzel/htmltruncate.py/master/htmltruncate.py
"""


__all__ = ["truncate"]

END = -1


class OpenTag:
    def __init__(self, tag, rest=''):
        self.tag = tag
        self.rest = rest

    def as_string(self):
        return '<' + self.tag + self.rest + '>'


class CloseTag(OpenTag):
    def as_string(self):
        return '</' + self.tag + '>'


class SelfClosingTag(OpenTag):
    pass


class Tokenizer:
    def __init__(self, input):
        self.input = input
        # points at the next unconsumed character of the input
        self.counter = 0

    def __next_char(self):
        self.counter += 1
        return self.input[self.counter]

    def next_token(self):
        try:
            char = self.input[self.counter]
            self.counter += 1
            if char == '&':
                return self.__entity()
            elif char != '<':
                return self.__word(char)
            elif self.input[self.counter] == '/':
                self.counter += 1
                return self.__close_tag()
            else:
                return self.__open_tag()
        except IndexError:
            return END

    def __word(self, char):
        word = char

        char = self.input[self.counter]
        while char not in ["<", " "]:
            word += char
            char = self.__next_char()

        return word

    def __entity(self):
        """Return a token representing an HTML character entity.
        Precondition: self.counter points at the charcter after the &
        Postcondition: self.counter points at the character after the ;
        """
        char = self.input[self.counter]
        entity = ['&']
        while char != ';':
            entity.append(char)
            char = self.__next_char()
        entity.append(';')
        self.counter += 1
        return ''.join(entity)

    def __open_tag(self):
        """Return an open/close tag token.
        Precondition: self.counter points at the first character of the tag
        name
        Postcondition: self.counter points at the character after the <tag>
        """
        char = self.input[self.counter]
        tag = []
        rest = []
        while char != '>' and char != ' ':
            tag.append(char)
            char = self.__next_char()
        while char != '>':
            rest.append(char)
            char = self.__next_char()
        if self.input[self.counter - 1] == '/':
            self.counter += 1
            return SelfClosingTag(''.join(tag), ''.join(rest))
        else:
            self.counter += 1
            return OpenTag(''.join(tag), ''.join(rest))

    def __close_tag(self):
        """Return an open/close tag token.
        Precondition: self.counter points at the first character of the tag
        name
        Postcondition: self.counter points at the character after the <tag>
        """
        char = self.input[self.counter]
        tag = []
        while char != '>':
            tag.append(char)
            char = self.__next_char()
        self.counter += 1
        return CloseTag(''.join(tag))


def truncate(str, target_len, ellipsis=''):
    """Returns a copy of str truncated to target_len words,
    preserving HTML markup (which does not count towards the length).
    Any tags that would be left open by truncation will be closed at
    the end of the returned string.  Optionally append ellipsis if
    the string was truncated."""
    # open tags are pushed on here, then popped when the matching close tag is
    # found
    stack = []
    # string to be returned
    retval = []
    # number of words (not counting markup) placed in retval so far
    length = 0
    tokens = Tokenizer(str)
    tok = tokens.next_token()

    while tok != END:
        if not length < target_len:
            retval.append(ellipsis)
            break
        if tok.__class__.__name__ == 'OpenTag':
            stack.append(tok)
            retval.append(tok.as_string())
        elif tok.__class__.__name__ == 'CloseTag':
            if len(stack) and stack[-1].tag == tok.tag:
                stack.pop()
                retval.append(tok.as_string())
        elif tok.__class__.__name__ == 'SelfClosingTag':
            retval.append(tok.as_string())
        else:
            retval.append(tok)
            if tok != " ":
                length += 1

        tok = tokens.next_token()

    while len(stack) > 0:
        tok = CloseTag(stack.pop().tag)
        retval.append(tok.as_string())

    return ''.join(retval)
