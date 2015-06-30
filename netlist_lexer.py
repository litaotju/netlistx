# -*- coding: utf-8 -*-
"""
Created on Sun Jun 28 15:22:50 2015

@author: litao
"""
import lex
states = (
   ('linecomment','exclusive'),
   ('blockcomment','exclusive'),
   ('timescale','exclusive'),
)

literals = ['.',';','(',')','[',':',']','=',"'"]
token_raw = [
   'NUMBER',
   'IDENTIFIER',
   'VECTOR',
   'HEX_NUMBER'
   ]
reserved={
   'module' : 'MODULE',
   'wire' : 'WIRE',
   'input' : 'INPUT',
   'output' : 'OUTPUT',
   'inout' :'INOUT',
   'defparam':'DEFPARAM',
   'assign':'ASSIGN',
   'endmoule':'ENDMOULE'   
}
tokens=token_raw+list(reserved.values())
##########################################################
#注释与timescale部分,没有返回token
def t_timescale(t):
    r'\`'
    t.lexer.begin('timescale')
#comment section
def t_linecomment(t):
    r'\/\/.*'
    t.lexer.begin('linecomment')
def t_timescale_linecomment_error(t):
    t.lexer.skip(1)
    pass
def t_timescale_linecomment_end(t):
    r'\n'
    t.lexer.lineno += 1
    t.lexer.begin('INITIAL') 

def t_blockcomment(t):
    r'\/\*'
    t.lexer.begin('blockcomment')
def t_blockcomment_error(t):
    t.lexer.skip(1)
    pass
def t_blockcomment_end(t):
    r'\*\/'
    t.lexer.begin('INITIAL')
##########################################################
def t_words(t):
    '\\\\?[\w]+[\\\\\w\d_\.\[\]]*'
    t.type = reserved.get(t.value,'IDENTIFIER')
    return t
def t_NUMBER(t):
    r'\d+'
    t.value=int(t.value)
    return t
def t_HEX_NUMBER(t):
    r'\d+\'[0-9A-F]+'
    return t
def t_VECTOR(t):
    r'\[\d+\:\d+\]'
    return t
##########################################################
#标点符号部分    
def t_lbracket(t):
    r'\('
    t.type='('
    return t
def t_rbracket(t):
    r'\)'
    t.type=')'
    return t
def t_lseqbracket(t):
    r'\['
    t.type='['
    return t
def t_rseqbracket(t):
    r'\]'
    t.type=']'
    return t
#def t_comma(t):
#    r'\,'
#    t.type=','
#    return t
def t_period(t):
    r'\.'
    t.type='.'
    return t
def t_colon(t):
    r'\:'
    t.type=':'
    return t
def t_semicolon(t):
    r'\;'
    t.type=';'
    return t
def t_equal(t):
    r'\='
    t.type='='
    return t
def t_singlequote(t):
    r'\''
    t.type="'"
    return t
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)    
##########################################################
#忽略空白 和 打印错误
def t_userignore(t):
    r'\s'
    pass
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)
# Build the lexer
lexer = lex.lex()


##########################################################
if __name__=="__main__":
    # Give the lexer some input
    fname=raw_input("plz enter file name:")
    fobj=open(fname)
    fobj2=open(fname+"rewrite",'w+')
    all_lines=fobj.read()
    #print all_lines
    lexer.input(all_lines)
    for tok in lexer:
        fobj2.write(tok.value)
        print tok.value
    fobj2.close()
    fobj.close()
