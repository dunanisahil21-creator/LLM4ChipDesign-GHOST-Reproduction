// Original self-checking testbench for uart_tx.v.
// Sends two bytes, samples tx at the midpoint of each bit cell,
// and checks both the start bit and the eight data bits.

`timescale 1ns/1ps

module uart_tx_tb;

    localparam BAUD = 16;

    reg        clk;
    reg        rst_n;
    reg        start;
    reg  [7:0] din;
    wire       tx;
    wire       busy;

    integer    errors;
    integer    bit_idx;
    reg  [7:0] expected;
    reg        got_bit;

    uart_tx #(.BAUD_DIV(BAUD)) dut (
        .clk(clk), .rst_n(rst_n),
        .start(start), .din(din),
        .tx(tx), .busy(busy)
    );

    always #5 clk = ~clk;

    task send_and_check;
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
            if (tx !== 1'b0) begin
                $display("FAIL: start bit was not 0 for data %02h (tx=%b)", data, tx);
                errors = errors + 1;
            end else begin
                $display("OK  : start bit for %02h", data);
            end

            // Sample each of the 8 data bits in the middle of its cell.
            for (bit_idx = 0; bit_idx < 8; bit_idx = bit_idx + 1) begin
                repeat (BAUD) @(posedge clk);
                got_bit = tx;
                if (got_bit !== expected[bit_idx]) begin
                    $display("FAIL: data %02h bit %0d exp=%b got=%b",
                             data, bit_idx, expected[bit_idx], got_bit);
                    errors = errors + 1;
                end else begin
                    $display("OK  : data %02h bit %0d = %b",
                             data, bit_idx, got_bit);
                end
            end

            // Wait for the stop bit and return to idle.
            repeat (BAUD * 2) @(posedge clk);
        end
    endtask

    initial begin
        clk    = 0;
        rst_n  = 0;
        start  = 0;
        din    = 0;
        errors = 0;

        #20 rst_n = 1;

        send_and_check(8'hA5);
        send_and_check(8'h3C);

        if (errors == 0) $display("All tests passed!");
        else             $display("%0d test(s) failed.", errors);
        $finish;
    end

endmodule
