module SCAN_FD (Q, C, D,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, D;



// Instantiate the module
FD instance_name (
    .Q(Q), 
    .C(C), 
    .D(SCAN_EN?SCAN_IN:D)    );



assign SCAN_OUT=Q;
endmodule
module SCAN_FDC (Q, C, CLR, D,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CLR, D;



// Instantiate the module
FDC instance_name (
    .Q(Q), 
    .C(C), 
    .CLR(CLR), 
    .D(SCAN_EN?SCAN_IN:D)    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDCE (Q, C, CE, CLR, D,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CE, CLR, D;



// Instantiate the module
FDCE instance_name (
    .Q(Q), 
    .C(C), 
    .CE(CE), 
    .CLR(CLR), 
    .D(SCAN_EN?SCAN_IN:D)    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDCE_1 (Q, C, CE, CLR, D,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CE, CLR, D;



// Instantiate the module
FDCE_1 instance_name (
    .Q(Q), 
    .C(C), 
    .CE(CE), 
    .CLR(CLR), 
    .D(SCAN_EN?SCAN_IN:D)    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDCP (Q, C, CLR, D, PRE,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CLR, D, PRE;



// Instantiate the module
FDCP instance_name (
    .Q(Q), 
    .C(C), 
    .CLR(CLR), 
    .D(SCAN_EN?SCAN_IN:D),    .PRE(PRE)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDCPE (Q, C, CE, CLR, D, PRE,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CE, CLR, D, PRE;



// Instantiate the module
FDCPE instance_name (
    .Q(Q), 
    .C(C), 
    .CE(CE), 
    .CLR(CLR), 
    .D(SCAN_EN?SCAN_IN:D),    .PRE(PRE)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDCPE_1 (Q, C, CE, CLR, D, PRE,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CE, CLR, D, PRE;



// Instantiate the module
FDCPE_1 instance_name (
    .Q(Q), 
    .C(C), 
    .CE(CE), 
    .CLR(CLR), 
    .D(SCAN_EN?SCAN_IN:D),    .PRE(PRE)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDCP_1 (Q, C, CLR, D, PRE,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CLR, D, PRE;



// Instantiate the module
FDCP_1 instance_name (
    .Q(Q), 
    .C(C), 
    .CLR(CLR), 
    .D(SCAN_EN?SCAN_IN:D),    .PRE(PRE)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDC_1 (Q, C, CLR, D,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CLR, D;



// Instantiate the module
FDC_1 instance_name (
    .Q(Q), 
    .C(C), 
    .CLR(CLR), 
    .D(SCAN_EN?SCAN_IN:D)    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDDRCPE (Q, C0, C1, CE, CLR, D0, D1, PRE,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C0, C1, CE, CLR, D0, D1, PRE;



// Instantiate the module
FDDRCPE instance_name (
    .Q(Q), 
    .C0(C0), 
    .C1(C1), 
    .CE(CE), 
    .CLR(CLR), 
    .D0(D0), 
    .D1(D1), 
    .PRE(PRE)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDDRRSE (Q, C0, C1, CE, D0, D1, R, S,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C0, C1, CE, D0, D1, R, S;



// Instantiate the module
FDDRRSE instance_name (
    .Q(Q), 
    .C0(C0), 
    .C1(C1), 
    .CE(CE), 
    .D0(D0), 
    .D1(D1), 
    .R(R), 
    .S(S)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDE (Q, C, CE, D,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CE, D;



// Instantiate the module
FDE instance_name (
    .Q(Q), 
    .C(C), 
    .CE(CE), 
    .D(SCAN_EN?SCAN_IN:D)    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDE_1 (Q, C, CE, D,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CE, D;



// Instantiate the module
FDE_1 instance_name (
    .Q(Q), 
    .C(C), 
    .CE(CE), 
    .D(SCAN_EN?SCAN_IN:D)    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDP (Q, C, D, PRE,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, D, PRE;



// Instantiate the module
FDP instance_name (
    .Q(Q), 
    .C(C), 
    .D(SCAN_EN?SCAN_IN:D),    .PRE(PRE)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDPE (Q, C, CE, D, PRE,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CE, D, PRE;



// Instantiate the module
FDPE instance_name (
    .Q(Q), 
    .C(C), 
    .CE(CE), 
    .D(SCAN_EN?SCAN_IN:D),    .PRE(PRE)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDPE_1 (Q, C, CE, D, PRE,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CE, D, PRE;



// Instantiate the module
FDPE_1 instance_name (
    .Q(Q), 
    .C(C), 
    .CE(CE), 
    .D(SCAN_EN?SCAN_IN:D),    .PRE(PRE)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDP_1 (Q, C, D, PRE,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, D, PRE;



// Instantiate the module
FDP_1 instance_name (
    .Q(Q), 
    .C(C), 
    .D(SCAN_EN?SCAN_IN:D),    .PRE(PRE)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDR (Q, C, D, R,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, D, R;



// Instantiate the module
FDR instance_name (
    .Q(Q), 
    .C(C), 
    .D(SCAN_EN?SCAN_IN:D),    .R(R)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDRE (Q, C, CE, D, R,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CE, D, R;



// Instantiate the module
FDRE instance_name (
    .Q(Q), 
    .C(C), 
    .CE(CE), 
    .D(SCAN_EN?SCAN_IN:D),    .R(R)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDRE_1 (Q, C, CE, D, R,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CE, D, R;



// Instantiate the module
FDRE_1 instance_name (
    .Q(Q), 
    .C(C), 
    .CE(CE), 
    .D(SCAN_EN?SCAN_IN:D),    .R(R)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDRS (Q, C, D, R, S,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, D, R, S;



// Instantiate the module
FDRS instance_name (
    .Q(Q), 
    .C(C), 
    .D(SCAN_EN?SCAN_IN:D),    .R(R), 
    .S(S)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDRSE (Q, C, CE, D, R, S,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CE, D, R, S;



// Instantiate the module
FDRSE instance_name (
    .Q(Q), 
    .C(C), 
    .CE(CE), 
    .D(SCAN_EN?SCAN_IN:D),    .R(R), 
    .S(S)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDRSE_1 (Q, C, CE, D, R, S,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CE, D, R, S;



// Instantiate the module
FDRSE_1 instance_name (
    .Q(Q), 
    .C(C), 
    .CE(CE), 
    .D(SCAN_EN?SCAN_IN:D),    .R(R), 
    .S(S)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDRS_1 (Q, C, D, R, S,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, D, R, S;



// Instantiate the module
FDRS_1 instance_name (
    .Q(Q), 
    .C(C), 
    .D(SCAN_EN?SCAN_IN:D),    .R(R), 
    .S(S)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDR_1 (Q, C, D, R,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, D, R;



// Instantiate the module
FDR_1 instance_name (
    .Q(Q), 
    .C(C), 
    .D(SCAN_EN?SCAN_IN:D),    .R(R)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDS (Q, C, D, S,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, D, S;



// Instantiate the module
FDS instance_name (
    .Q(Q), 
    .C(C), 
    .D(SCAN_EN?SCAN_IN:D),    .S(S)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDSE (Q, C, CE, D, S,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CE, D, S;



// Instantiate the module
FDSE instance_name (
    .Q(Q), 
    .C(C), 
    .CE(CE), 
    .D(SCAN_EN?SCAN_IN:D),    .S(S)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDSE_1 (Q, C, CE, D, S,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, CE, D, S;



// Instantiate the module
FDSE_1 instance_name (
    .Q(Q), 
    .C(C), 
    .CE(CE), 
    .D(SCAN_EN?SCAN_IN:D),    .S(S)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FDS_1 (Q, C, D, S,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, D, S;



// Instantiate the module
FDS_1 instance_name (
    .Q(Q), 
    .C(C), 
    .D(SCAN_EN?SCAN_IN:D),    .S(S)
    );


assign SCAN_OUT=Q;
endmodule
module SCAN_FD_1 (Q, C, D,SCAN_EN,SCAN_IN,SCAN_OUT);
input SCAN_EN;
input SCAN_IN;
output SCAN_OUT;
    output Q;
    input  C, D;



// Instantiate the module
FD_1 instance_name (
    .Q(Q), 
    .C(C), 
    .D(SCAN_EN?SCAN_IN:D)    );


assign SCAN_OUT=Q;
endmodule
