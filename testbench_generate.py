import os.path
#################################################
def generate_testbench(top_module,fd_cnt,output_dir):
    reg_list=[]
    assert (top_module.cellref=='module' and top_module.m_type=='top_module'),\
    "%s is not top modoule" % top_module.name
    output_file=os.path.join(output_dir,top_module.name+"_test_bench.v")
    fobj=open(output_file,'w')
    fobj.writelines("module "+top_module.name+"_tb;\n")
    fobj.writelines("parameter fd_cnt="+str(fd_cnt)+";\n")
    fobj.writelines("reg scan_en,scan_in;\n")
    fobj.writelines("wire scan_out;\n")
    for port in top_module.port_list:
        if port.port_type=='input':
            reg_list.append(port.port_name)
            if port.port_width!=1:
                WIDTH=port.port_width
                x="reg ["+str(WIDTH)+":0] "+port.port_name+";\n"
            else:
                x="reg "+port.port_name+";\n"
        elif port.port_type=="output":
            if port.port_width!=1:
                WIDTH=port.port_width
                x="wire ["+str(WIDTH)+":0] "+port.port_name+";\n"
                x=x+"wire ["+str(WIDTH)+":0] "+port.port_name+"_g;\n"
            else:
                x="wire "+port.port_name+";\n"
                x=x+"wire "+port.port_name+"_g;\n" 
        fobj.writelines(x)

    ################################################
    #create instance
    m1_decl=top_module.name+" uut_golden "
    m2_decl=top_module.name+"_scan uut_scan "
    fobj.writelines(m1_decl+"(\n")
    for port in top_module.port_list:
        if port.port_type=='output':
            x="."+port.port_name+"("+port.port_name+"_g),\n"
        else:
            x="."+port.port_name+"("+port.port_name+"),\n"
        fobj.writelines(x)
    fobj.writelines(");\n")

    fobj.writelines(m2_decl+"(\n")
    fobj.writelines(".scan_in(scan_in),\n.scan_en(scan_en),\n.scan_out(scan_out),\n")
    for port in top_module.port_list:
        x="."+port.port_name+"("+port.port_name+"),\n"
        fobj.writelines(x)
    fobj.writelines(");\n")

    
    ################################################
    #create initial value
    fobj.writelines("initial begin\n")
    for reg in reg_list:
        x=reg+"=0;\n"
        fobj.writelines(x)
    fobj.writelines("#100 reset=1;\n#35 reset=0;\n")
    fobj.writelines("end\n")

    ################################################
    #create stimulus   
    stimulus="""
initial #1000 scan_en=1;
reg [3:0] scan_in_reg;
always @(negedge clock)begin
if(reset) begin
    scan_in_reg<=4'b0110;
    scan_in<=1'b0;
    end
else begin
	scan_in_reg<={scan_in_reg[0],scan_in_reg[3:1]};
	scan_in<=scan_in_reg[0];
	end
end
reg [19:0]cnt;
always @(posedge clock)begin
    if(reset)cnt<=0;
    else if(scan_en)cnt<=cnt+1;
    else cnt<=cnt;
end
wire scan_out_rdy;
assign scan_out_rdy=cnt>=fd_cnt?1'b1:1'b0;
"""
    fobj.writelines(stimulus)

    fobj.writelines("endmodule")
    fobj.close()
    print "Note: generate_testbench() successfully!"
    return True
