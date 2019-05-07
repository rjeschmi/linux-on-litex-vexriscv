#!/usr/bin/env python3

import argparse
import os

from migen import *

from litex.boards.targets import ulx3s

from litex.soc.interconnect import wishbone
from litex.soc.integration.soc_core import mem_decoder
from litex.soc.integration.builder import Builder

# LinuxSoC -----------------------------------------------------------------------------------------

class LinuxSoC(ulx3s.BaseSoC):
    csr_map = {
        "ddrphy": 16,
        "cpu":    17,
    }
    csr_map.update(ulx3s.BaseSoC.csr_map)

    ulx3s.BaseSoC.mem_map = {
        "rom":          0x00000000,
        "sram":         0x10000000,
        "emulator_ram": 0x20000000,
        "spiflash":     0x50000000,
        "main_ram":     0xc0000000,
        "csr":          0xf0000000,
    }

    def __init__(self, toolchain="trellis"):
        ulx3s.BaseSoC.__init__(self, cpu_type="vexriscv", cpu_variant="linux", toolchain=toolchain)
        self.cpu.use_external_variant("VexRiscv.v")

        # machine mode emulator ram
        self.submodules.emulator_ram = wishbone.SRAM(0x4000)
        self.register_mem("emulator_ram", self.mem_map["emulator_ram"], self.emulator_ram.bus, 0x4000)

        # spiflash
        # spiflash_pads = self.platform.request("spiflash4x")
        # spiflash_pads.clk = Signal()
        # self.specials += Instance("STARTUPE2",
        #    i_CLK=0,
        #    i_GSR=0,
        #    i_GTS=0,
        #    i_KEYCLEARB=0,
        #    i_PACK=0,
        #    i_USRCCLKO=spiflash_pads.clk,
        #    i_USRCCLKTS=0,
        #    i_USRDONEO=1,
        #    i_USRDONETS=1)

        # self.submodules.spiflash = SpiFlash(
        #        spiflash_pads,
        #        dummy=11,
        #        div=2,
        #        endianness=self.cpu.endianness)
        # self.add_wb_slave(mem_decoder(self.mem_map["spiflash"]), self.spiflash.bus)
        # self.add_memory_region("spiflash", self.mem_map["spiflash"] | self.shadow_base, 0x1000000)

        # self.add_constant("FLASHBOOT_LINUX_VEXRISCV", None)
        # self.add_constant("FLASH_BOOT_ADDRESS", None)

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on Versa ECP5")
    parser.add_argument("--build", action="store_true", help="build bitstream")
    parser.add_argument("--load", action="store_true", help="load bitstream (SRAM)")
    parser.add_argument("--diamond", action="store_true", help="use Diamond instead of Trellis")

    args = parser.parse_args()

    if args.diamond:
        toolchain_path = "/usr/local/diamond/3.10_x64/bin/lin64"
    else:
        toolchain_path = "/usr/share/trellis"

    if args.build:
        soc = LinuxSoC(toolchain="diamond" if args.diamond else "trellis")
        builder = Builder(soc, output_dir="build_ulx3s")
        builder.build(toolchain_path=toolchain_path)
        if args.diamond:
            os.system("python3 bit_to_svf.py build_ulx3s/gateware/top.bit build_ulx3s/gateware/top.svf")

    if args.load:
        os.system("openocd -f openocd/ulx3s.cfg -c \"transport select jtag; init; svf build_ulx3s/gateware/top.svf; exit\"")

if __name__ == "__main__":
    main()