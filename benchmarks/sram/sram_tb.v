// Original self-checking testbench for sram.v.
// Eval1 reuses this testbench on the HT-infected RTL to confirm that
// normal (non-trigger) behaviour is preserved.

`timescale 1ns/1ps

module sram_tb;

    reg         clk;
    reg         rst_n;
    reg         we;
    reg  [4:0]  addr;
    reg  [7:0]  din;
    wire [7:0]  dout;

    integer errors;
    integer i;

    sram dut (
        .clk(clk), .rst_n(rst_n),
        .we(we), .addr(addr), .din(din), .dout(dout)
    );

    always #5 clk = ~clk;

    task write;
        input [4:0] a;
        input [7:0] d;
        begin
            @(negedge clk);
            we   = 1'b1;
            addr = a;
            din  = d;
            @(negedge clk);
            we = 1'b0;
        end
    endtask

    task check_read;
        input [4:0] a;
        input [7:0] exp;
        begin
            @(negedge clk);
            we   = 1'b0;
            addr = a;
            @(posedge clk);
            #1;
            if (dout !== exp) begin
                $display("FAIL: addr=%0d exp=%02h got=%02h", a, exp, dout);
                errors = errors + 1;
            end else begin
                $display("OK  : addr=%0d exp=%02h got=%02h", a, exp, dout);
            end
        end
    endtask

    initial begin
        clk    = 0;
        rst_n  = 0;
        we     = 0;
        addr   = 0;
        din    = 0;
        errors = 0;

        #12 rst_n = 1;

        // Write a simple pattern.
        for (i = 0; i < 8; i = i + 1) begin
            write(i[4:0], 8'hA0 + i[7:0]);
        end

        // Read it back and compare.
        for (i = 0; i < 8; i = i + 1) begin
            check_read(i[4:0], 8'hA0 + i[7:0]);
        end

        // Overwrite then re-read one location to confirm RMW semantics.
        write(5'd3, 8'hDE);
        check_read(5'd3, 8'hDE);

        if (errors == 0) $display("All tests passed!");
        else             $display("%0d test(s) failed.", errors);
        $finish;
    end

endmodule
