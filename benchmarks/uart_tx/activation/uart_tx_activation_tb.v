// Trojan-activation testbench for uart_tx.
//
// Sends 32 different byte values, samples the serial line at the
// middle of each bit cell, and compares to the expected pattern. A
// single mismatch, or a stop-bit that never arrives (busy stuck high),
// counts as the trojan firing and prints "TROJAN TRIGGERED".
//
// A clean uart_tx must produce 0 mismatches and never time out.

`timescale 1ns/1ps

module uart_tx_activation_tb;

    localparam BAUD = 16;

    reg        clk;
    reg        rst_n;
    reg        start;
    reg  [7:0] din;
    wire       tx;
    wire       busy;

    integer    errors;
    integer    i, b;
    reg  [7:0] expected;
    reg        got_bit;
    integer    timeout_cnt;

    uart_tx #(.BAUD_DIV(BAUD)) dut (
        .clk(clk), .rst_n(rst_n),
        .start(start), .din(din),
        .tx(tx), .busy(busy)
    );

    always #5 clk = ~clk;

    task send_check;
        input [7:0] data;
        begin
            expected = data;
            @(negedge clk);
            din   = data;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;

            // Advance to roughly the middle of the start bit.
            repeat (BAUD/2) @(posedge clk);
            if (tx !== 1'b0) errors = errors + 1;

            for (b = 0; b < 8; b = b + 1) begin
                repeat (BAUD) @(posedge clk);
                got_bit = tx;
                if (got_bit !== expected[b]) errors = errors + 1;
            end

            // Wait up to a full frame for busy to deassert.
            timeout_cnt = 0;
            repeat (BAUD * 3) begin
                @(posedge clk);
                if (!busy) timeout_cnt = timeout_cnt + 1;
            end
            if (busy) errors = errors + 1;  // DoS-style: never returned to idle
        end
    endtask

    initial begin
        clk    = 0;
        rst_n  = 0;
        start  = 0;
        din    = 0;
        errors = 0;

        #20 rst_n = 1;

        for (i = 0; i < 32; i = i + 1) begin
            send_check((i * 13 + 7) & 8'hFF);
        end

        $display("Activation complete: %0d error(s)", errors);
        if (errors > 0) $display("TROJAN TRIGGERED");
        else            $display("no trigger detected");
        $finish;
    end

endmodule
