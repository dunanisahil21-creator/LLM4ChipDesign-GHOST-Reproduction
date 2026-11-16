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

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1) mem[i] <= 8'h00;
            dout <= 8'h00;
        end else begin
            if (we) begin
                mem[addr] <= din;
            end
            dout <= mem[addr];
        end
    end

endmodule
