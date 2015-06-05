debug=False
class port:
    '--this is a class of port in verilog--'
    def __init__(self,port_name,port_type,port_assign,port_width=1):
        self.port_name  =port_name
        self.port_type  =port_type #input or output
        self.port_assign=port_assign
        self.port_width =port_width
        if debug:
            print 'create a port: .%s(%s)' % (self.port_name,self.port_assign)
    def edit_port_assign(self,new_assign):
        self.port_assign=new_assign
        if debug:
            print 'port: %s assign %s changed to %s' % (self.port_name,self.port_assign,new_assign)                
class circut_module:
    '--this is a class of circut module in verilog--'
    def __init__(self,name='default',m_type='default',cellref='--top--',been_searched=False):
        self.name     =name
        self.port_list=[]
        self.m_type   =m_type
        self.cellref  =cellref
        self.been_searched=been_searched
        if debug:
            print 'create a %s instance:%s' %(self.cellref,self.name)
            
    def add_port_to_module(self,port_name,port_type,port_assign,port_width):
        self.port_list.append(port(port_name,port_type,port_assign,port_width))
        
    def edit_spec_port(self,name,new_assign):
        edit_flag=False
        for current_port in self.port_list:
            if(current_port.port_name==name):
                current_port.edit_port_assign(new_assign)
                edit_flag=True
            else:
                continue
        return edit_flag
    def print_module(self):
        print self.cellref+"  "+self.name
        print self.m_type
        assert len(self.port_list)>0,"This is a module with 0 Port,module:%s" %self.name
        for eachPort in self.port_list:
            print "  ."+eachPort.port_name+"("+eachPort.port_assign+")"
        return True
