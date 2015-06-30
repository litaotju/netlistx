# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 21:13:37 2015

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
   'endmodule':'ENDMODULE'   
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
def t_HEX_NUMBER(t):
    r'\d+\'h[0-9A-F]+'
    return t
def t_words(t):
    '\\\\?[a-zA-Z_]+[\\\\\w\d_\.\[\]]*'
    t.type = reserved.get(t.value,'IDENTIFIER')
    return t
def t_NUMBER(t):
    r'\d+'
    t.value=int(t.value)
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


import yacc
def p_vmfile(p):
    '''vm_file : module_decl port_decl_list signal_decl_list primitive_list assign_stm_list ENDMODULE
               | module_decl port_decl_list signal_decl_list primitive_list ENDMODULE
    '''
    print "Parse vm netlist successfully"
def p_module_decl(p):
    "module_decl : MODULE IDENTIFIER '(' pipo_list ')' ';'"
    pass

def p_pipo_list(p):
    '''pipo_list : pipo_list IDENTIFIER
                 | IDENTIFIER
    '''
    pass

def p_port_decl(p):
    '''port_decl_list : port_decl_list port_decl
                     | port_decl
       port_decl     : INPUT  IDENTIFIER ';'
                     | INPUT  VECTOR IDENTIFIER ';'
                     | OUTPUT IDENTIFIER ';'
                     | OUTPUT VECTOR IDENTIFIER ';'
                     | INOUT  IDENTIFIER ';'
                     | INOUT  VECTOR IDENTIFIER ';'
    '''
    pass
def p_signal_decl_list(p):
    '''signal_decl_list : signal_decl_list signal_decl
                        | signal_decl
        signal_decl    : WIRE VECTOR IDENTIFIER ';'
                       | WIRE IDENTIFIER ';'
    '''
    pass
def p_primitive_list(p):
    '''primitive_list : primitive_list primitive
                      | primitive
       primitive      : IDENTIFIER IDENTIFIER '(' primitive_port_list ')' ';'
                      | IDENTIFIER IDENTIFIER '(' primitive_port_list ')' ';' defparam
       defparam       : DEFPARAM IDENTIFIER '.' IDENTIFIER '=' HEX_NUMBER ';'
    '''
    pass
def p_primitive_port_list(p):
    '''primitive_port_list : primitive_port_list primitive_port
                           | primitive_port
       primitive_port     : '.' IDENTIFIER '(' IDENTIFIER ')' 
    '''
    pass
def p_assign_stm_list(p):
    '''assign_stm_list  : assign_stm_list assign_stm
                        | assign_stm
        assign_stm      : ASSIGN IDENTIFIER '=' IDENTIFIER ';'
    '''
    pass
    
def p_error(p):
    print("Syntax error in input!")

# Build the parser
parser = yacc.yacc()

if __name__=='__main__':
    fname=raw_input("plz enter file name to parse:")
    fobj=open(fname)
    all_lines=fobj.read()
    #print all_lines
    parser.parse(all_lines,debug=True)
#    print result
    fobj.close()
