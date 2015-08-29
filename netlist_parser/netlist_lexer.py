# -*- coding: utf-8 -*-
import lex
states = (
   ('timescale','exclusive'),
   ('string','exclusive')
)

literals = [',','.',';','(',')','[',':',']','=',"'",'{','}','"']
token_raw = [
   'NUMBER',
   'IDENTIFIER',
   'VECTOR',
   'BIT',
   'HEX_NUMBER',
   'BIN_NUMBER',
   'STRING_CON'
   ]
reserved={
   'module' : 'MODULE',
   'wire' : 'WIRE',
   'input' : 'INPUT',
   'output' : 'OUTPUT',
   'inout' :'INOUT',
   'defparam':'DEFPARAM',
   'INIT'   :'INIT',
   'assign':'ASSIGN',
   'endmodule':'ENDMODULE',   
}
tokens=token_raw+list(reserved.values())
###############################################################################
#注释与timescale部分,没有返回token
def t_timescale(t):
    r'(\`timescale.*)'
    t.lexer.begin('timescale')
def t_timescale_end(t):
    r'\n'
    t.lexer.lineno += 1
    t.lexer.begin('INITIAL') 
#comment section
def t_linecomment(t):
    r'//.*\n'
    t.lexer.lineno += 1
def t_blockcomment(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')
#literal string section 
def t_to_string(t):
    r'"'
    t.type='"'
    t.lexer.begin('string')
    return t
def t_string_STRING_CON(t):
    r'[^"]+'
    return t
def t_string_end(t):
    r'"'
    t.type='"'
    t.lexer.begin('INITIAL')
    return t
###############################################################################
#有返回值的部分,除过纯数字之外,返回值都是text
def t_BIN_NUMBER(t):
    r'\d+\'b[0-1]+'
    return t
def t_HEX_NUMBER(t):
    r'\d+\'h[0-9A-F]+'
    return t
def t_words(t):
    # BUGY:把[\d]加入标识符会造成，端口信号的name和string完全相同
    '[\\\\]?(\w+(\[\d+\])?\.)*\w+$'
    t.type = reserved.get(t.value,'IDENTIFIER')
    return t
def t_NUMBER(t):
    r'\d+'
    t.value=int(t.value)
    return t
def t_VECTOR(t):
    r'\[\d+\:\d+\]'
    return t
def t_BIT(t):
    r'\[\d+\]'
    return t
###############################################################################
#标点符号部分
def t_flbracket(t):
    r'\{'
    t.type='{'
    return t
def t_frbracket(t):
    r'\}'
    t.type='}'
    return t    
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
def t_comma(t):
    r'\,'
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
def t_ANY_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)    
###############################################################################
#忽略空白 和 打印错误
def t_userignore(t):
    r'\s'
    pass
def t_ANY_error(t):
    print "Warning Illegal character '%s' in line : %d %s " %(t.value[0],t.lexer.lineno,lexer.lexstate)
    t.lexer.skip(1)
# Build the lexer
lexer = lex.lex()
###############################################################################
if __name__=='__main__':
    import sys
    import os
    if len(sys.argv)==1:
        print "Just handle one simple verilog netlist in os.get_cwd() dir"
        fname=raw_input("plz enter the file name:")
        with open(fname,'r') as fobj:
            all_lines=fobj.read()
            lex.runmain(lexer,all_lines)
    elif sys.argv[1]=='many': 
        parent_dir=os.getcwd()
        while(1):
            tmp1=raw_input('Plz enter the verilog source sub dir:')
            input_file_dir=parent_dir+"\\test_input_netlist\\"+tmp1
            if os.path.exists(input_file_dir)==False:
                print 'Error : this dir dont exists!'
                continue
            else:
                break
        for eachFile in os.listdir(input_file_dir):
            print  eachFile
            if os.path.splitext(eachFile)[1]=='.v':
                try:
                    fobj=open(fname,'r')
                except IOError,e:
                    print "Error: file open error:",e
                else:
                    all_lines=fobj.read()             
                    lex.runmain(lexer,all_lines)
                    fobj.close()
            else:
                continue
