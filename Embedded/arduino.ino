#include <mcp_can.h>
#include <mcp_can_dfs.h>
#include <SPI.h>

#define SPI_CS_PIN 9

MCP_CAN CAN(SPI_CS_PIN);

unsigned char stmp[8] = {0};

void setup()
{
    Serial.begin(115200);
    while (!Serial);

    while (CAN_OK != CAN.begin(CAN_500KBPS))
    {
        Serial.println("CAN BUS FAIL!");
        delay(100);
    }
    Serial.println("CAN BUS OK!");
    Serial.println("Type a number and press enter:");
}

void loop()
{
    if (Serial.available())
    {
        String input = Serial.readStringUntil('\n');
        float value = input.toFloat();

        // Apply multiplier/divisor scaling
        int32_t scaled = (int32_t)((value * 10) / 1);

        // Pack scaled value into bytes 0-3 (offset=0, length=4, mask=0xFFFFFFFF)
        stmp[0] = (scaled >> 24) & 0xFF;
        stmp[1] = (scaled >> 16) & 0xFF;
        stmp[2] = (scaled >> 8)  & 0xFF;
        stmp[3] = (scaled >> 0)  & 0xFF;

        // Clear remaining bytes
        for (int i = 4; i < 8; i++) stmp[i] = 0;

        CAN.sendMsgBuf(0x123, 0, 8, stmp);

        Serial.print("Sent value over CAN: ");
        Serial.println(scaled);
    }
}