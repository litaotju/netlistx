# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 21:13:37 2015

@author: litao
"""
import lex
states = (
   ('timescale','exclusive'),
   ('linecomment','exclusive'),
   ('blockcomment','exclusive'),
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
##########################################################
#注释与timescale部分,没有返回token
def t_timescale(t):
    r'(\`timescale.*)'
    t.lexer.begin('timescale')
#comment section
def t_linecomment(t):
    r'//.*'
    t.lexer.begin('linecomment')
def t_timescale_linecomment_end(t):
    r'\n'
    t.lexer.lineno += 1
    t.lexer.begin('INITIAL') 

def t_to_blockcomment(t):
    r'\/\*'
    t.lexer.begin('blockcomment')
def t_blockcomment_end(t):
    r'\*\/'
    t.lexer.begin('INITIAL')
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
##########################################################
def t_BIN_NUMBER(t):
    r'\d+\'b[0-1]+'
    return t
def t_HEX_NUMBER(t):
    r'\d+\'h[0-9A-F]+'
    return t
def t_words(t):
    '\\\\?[a-zA-Z_]+[\\\\\w\.]*'
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
##########################################################
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
##########################################################
#忽略空白 和 打印错误
def t_userignore(t):
    r'\s'
    pass
def t_ANY_error(t):
    #print "Illegal character '%s' in line : %d %s " %(t.value[0],t.lexer.lineno,lexer.lexstate)
    t.lexer.skip(1)
# Build the lexer
lexer = lex.lex()

#####################################################################################################
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
       primitive      : IDENTIFIER IDENTIFIER     '(' primitive_port_list ')' ';'
                      | IDENTIFIER IDENTIFIER BIT '(' primitive_port_list ')' ';' 
                      | IDENTIFIER IDENTIFIER     '(' primitive_port_list ')' ';'    defparam_list
                      | IDENTIFIER IDENTIFIER BIT '(' primitive_port_list ')' ';'    defparam_list
                      | IDENTIFIER IDENTIFIER VECTOR '(' primitive_port_list ')' ';' defparam_list
       defparam_list  : defparam_list defparam_stm
                      | defparam_stm
       defparam_stm   : DEFPARAM IDENTIFIER              '=' HEX_NUMBER ';'
                      | DEFPARAM IDENTIFIER        '.' INIT '=' HEX_NUMBER ';'
                      | DEFPARAM IDENTIFIER BIT    '.' INIT '=' HEX_NUMBER ';'
                      | DEFPARAM IDENTIFIER VECTOR '.' INIT '=' HEX_NUMBER ';'
                      | DEFPARAM IDENTIFIER VECTOR '.' IDENTIFIER '=' NUMBER ';'
                      | DEFPARAM IDENTIFIER VECTOR '.' IDENTIFIER '=' '"' STRING_CON '"' ';'
    '''
    pass
def p_primitive_port_list(p):
    '''primitive_port_list : primitive_port_list primitive_port
                           | primitive_port
       primitive_port     : '.' IDENTIFIER '(' IDENTIFIER ')' 
                          | '.' IDENTIFIER '(' IDENTIFIER BIT ')'
                          | '.' IDENTIFIER '(' IDENTIFIER VECTOR ')'
                          | '.' IDENTIFIER '(' joint_signal ')'
    '''
    pass
def p_joint_signal(p):
    '''joint_signal       : '{' joint_signal_list '}'
       joint_signal_list  : joint_signal_list signal_element
                          | signal_element
    '''
def p_signal_element(p):
    '''signal_element : IDENTIFIER BIT
                      | IDENTIFIER VECTOR
                      | IDENTIFIER
    '''
    pass
    
def p_assign_stm_list(p):
    '''assign_stm_list  : assign_stm_list assign_stm
                        | assign_stm
        assign_stm      : ASSIGN signal_element '=' signal_element ';'
                        | ASSIGN signal_element '=' BIN_NUMBER ';'
    '''
    pass
    
def p_error(p):
    if p:
         print "Syntax error at token %s :%s in line %d " % ( p.type , p.value,p.lexer.lineno)
         exit(0)
    else:
         print("Syntax error at EOF")

# Build the parser
parser = yacc.yacc()
if __name__=='__main__':
    fname=raw_input("plz enter file name to parse:")
    fobj=open(fname)
    all_lines=fobj.read()
    #print all_lines
    t=parser.parse(all_lines)
#    print result
    fobj.close()
