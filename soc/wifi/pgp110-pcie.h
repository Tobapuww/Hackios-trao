/*
 * The PGP110's PCIe0 and QCA6490 facts, from its own device tree (fdt-pgp110-20261105.dts).
 *
 * The same facts are in configs/pgp110-wifi-sm8475.json. Comments give the
 * device-tree property each value came from.
 */
#ifndef _PGP110_PCIE_H_
#define _PGP110_PCIE_H_

#define PGP110_PCIE_PARF_PHYS       0x1c00000ULL
#define PGP110_PCIE_PARF_SIZE       0x3000ULL
#define PGP110_PCIE_PHY_PHYS        0x1c06000ULL
#define PGP110_PCIE_PHY_SIZE        0x2000ULL
#define PGP110_PCIE_DM_CORE_PHYS    0x60000000ULL
#define PGP110_PCIE_DM_CORE_SIZE    0xf1dULL
#define PGP110_PCIE_ELBI_PHYS       0x60000f20ULL
#define PGP110_PCIE_ELBI_SIZE       0xa8ULL
#define PGP110_PCIE_IATU_PHYS       0x60001000ULL
#define PGP110_PCIE_IATU_SIZE       0x1000ULL
#define PGP110_PCIE_CONF_PHYS       0x60100000ULL
#define PGP110_PCIE_CONF_SIZE       0x100000ULL
#define PGP110_PCIE_BAR_PHYS        0x60200000ULL     /* BAR0, as Linux assigned it (dmesg 2026-11-05) */
#define PGP110_PCIE_BAR_SIZE        0x200000ULL

/* perst-gpio / wake-gpio / cnss wlan-en-gpio / xo-clk-gpio; clkreq is the pcie0_clkreqn mux gpio95 */
#define PGP110_PCIE_PERST_GPIO      94
#define PGP110_PCIE_WAKE_GPIO       96
#define PGP110_PCIE_CLKREQ_GPIO     95
#define PGP110_WLAN_EN_GPIO         80
#define PGP110_WLAN_BT_EN_GPIO      81
#define PGP110_WLAN_SW_CTRL_GPIO    82
#define PGP110_WLAN_XO_CLK_GPIO     204

/* qcom,phy-status-offset / -bit / -power-down-offset / -aux-clk-freq */
#define PGP110_PCIE_PHY_STATUS_OFFSET   0x214
#define PGP110_PCIE_PHY_STATUS_BIT      6
#define PGP110_PCIE_PHY_POWER_DOWN      0x240
#define PGP110_PCIE_AUX_CLK_FREQ        0x14

/* qcom,ep-latency (ms); the vendor log trains Gen2 x1 */
#define PGP110_PCIE_EP_LATENCY_MS       10
#define PGP110_PCIE_TARGET_SPEED        2
#define PGP110_PCIE_TARGET_WIDTH        1

/* qcom,smmu-sid-base, iommu-map; the radio's context is SID 0x1c01 */
#define PGP110_PCIE_SID_BASE            0x1c00
#define PGP110_PCIE_WLAN_SID            0x1c01
#define PGP110_PCIE_DMA_IOVA            0xa0000000ULL
#define PGP110_PCIE_DMA_SIZE            0x10000000ULL

/* interrupts: int_global_int is SPI 140 -> GIC INTID 172; PARF INT_ALL bit 23 is MSI0 */
#define PGP110_PCIE_SPI                 140
#define PGP110_PCIE_INTID               172

/* qcom,gdsc@17b004 and its qcom,collapse-vote <syscon@162128 bit> */
#define PGP110_PCIE_GDSC_PHYS           0x17b004UL
#define PGP110_PCIE_COLLAPSE_VOTE_PHYS  0x162128UL
#define PGP110_PCIE_COLLAPSE_VOTE_BIT   0

/* The vendor's PHY table (qcom,phy-sequence): offset, value, delay in microseconds. */
struct pgp110_pcie_phy_step { unsigned short offset; unsigned int value; unsigned short delay_us; };
static const struct pgp110_pcie_phy_step pgp110_pcie_phy_table[] = {
	{ 0x240, 0x00000003, 0 },
	{ 0x0c0, 0x00000001, 0 },
	{ 0x0cc, 0x00000031, 0 },
	{ 0x0d0, 0x00000001, 0 },
	{ 0x060, 0x000000ff, 0 },
	{ 0x064, 0x00000006, 0 },
	{ 0x000, 0x0000004c, 0 },
	{ 0x004, 0x00000006, 0 },
	{ 0x0e0, 0x00000090, 0 },
	{ 0x0e4, 0x00000082, 0 },
	{ 0x0f4, 0x00000007, 0 },
	{ 0x070, 0x00000002, 0 },
	{ 0x010, 0x00000002, 0 },
	{ 0x074, 0x00000016, 0 },
	{ 0x014, 0x00000016, 0 },
	{ 0x078, 0x00000036, 0 },
	{ 0x018, 0x00000036, 0 },
	{ 0x110, 0x00000008, 0 },
	{ 0x0bc, 0x0000000e, 0 },
	{ 0x120, 0x00000042, 0 },
	{ 0x080, 0x0000000a, 0 },
	{ 0x084, 0x0000001a, 0 },
	{ 0x020, 0x00000014, 0 },
	{ 0x024, 0x00000034, 0 },
	{ 0x088, 0x00000082, 0 },
	{ 0x028, 0x00000068, 0 },
	{ 0x090, 0x000000ab, 0 },
	{ 0x094, 0x000000ea, 0 },
	{ 0x098, 0x00000002, 0 },
	{ 0x030, 0x000000ab, 0 },
	{ 0x034, 0x000000aa, 0 },
	{ 0x038, 0x00000002, 0 },
	{ 0x140, 0x00000014, 0 },
	{ 0x164, 0x00000034, 0 },
	{ 0x03c, 0x00000001, 0 },
	{ 0x01c, 0x00000004, 0 },
	{ 0x174, 0x00000016, 0 },
	{ 0x1bc, 0x0000000f, 0 },
	{ 0x170, 0x000000a0, 0 },
	{ 0x11a4, 0x00000038, 0 },
	{ 0x10dc, 0x00000011, 0 },
	{ 0x1160, 0x000000bf, 0 },
	{ 0x1164, 0x000000bf, 0 },
	{ 0x1168, 0x000000b7, 0 },
	{ 0x116c, 0x000000ea, 0 },
	{ 0x115c, 0x0000003f, 0 },
	{ 0x1174, 0x0000005c, 0 },
	{ 0x1178, 0x0000009c, 0 },
	{ 0x117c, 0x0000001a, 0 },
	{ 0x1180, 0x00000089, 0 },
	{ 0x1170, 0x000000dc, 0 },
	{ 0x1188, 0x00000094, 0 },
	{ 0x118c, 0x0000005b, 0 },
	{ 0x1190, 0x0000001a, 0 },
	{ 0x1194, 0x00000089, 0 },
	{ 0x10cc, 0x000000f0, 0 },
	{ 0x1008, 0x00000009, 0 },
	{ 0x1014, 0x00000005, 0 },
	{ 0x104c, 0x00000008, 0 },
	{ 0x1050, 0x00000008, 0 },
	{ 0x10d8, 0x0000000f, 0 },
	{ 0x1118, 0x0000001c, 0 },
	{ 0x10f8, 0x00000007, 0 },
	{ 0x11f8, 0x00000008, 0 },
	{ 0xe84, 0x00000015, 0 },
	{ 0xe90, 0x0000003f, 0 },
	{ 0xee4, 0x00000002, 0 },
	{ 0xe40, 0x00000006, 0 },
	{ 0xe3c, 0x00000018, 0 },
	{ 0x2dc, 0x00000005, 0 },
	{ 0x388, 0x00000077, 0 },
	{ 0x398, 0x0000000b, 0 },
	{ 0x3e0, 0x0000000f, 0 },
	{ 0x60c, 0x0000001d, 0 },
	{ 0x614, 0x00000007, 0 },
	{ 0x620, 0x000000c1, 0 },
	{ 0x694, 0x00000000, 0 },
	{ 0x3d0, 0x0000008c, 0 },
	{ 0x1424, 0x00000001, 0 },
	{ 0x1428, 0x00000001, 0 },
	{ 0x200, 0x00000000, 0 },
	{ 0x244, 0x00000003, 0 },
};
#define PGP110_PCIE_PHY_STEPS 82

/* The WLAN supplies (vdd-wlan-*-supply). The regulator names are the PMIC regulators the tree
 * points at; their RPMh resource names are looked up in cmd-db at run time. */
struct pgp110_wlan_rail { const char *name; const char *regulator; unsigned min_uv, max_uv; };
static const struct pgp110_wlan_rail pgp110_wlan_rails[] = {
	{ "vdd-wlan-aon", "pmr735a_s2", 1012000u, 1040000u },
	{ "vdd-wlan-dig", "pm8350_s11", 966000u, 1170000u },
	{ "vdd-wlan-io", "pm8350_s10", 1800000u, 1800000u },
	{ "vdd-wlan-rfa1", "pm8350c_s1", 1900000u, 2024000u },
	{ "vdd-wlan-rfa2", "pm8350_s12", 1350000u, 2040000u },
	{ "wlan-ant-switch", "pmr735a_l7", 2800000u, 2800000u },
};
#define PGP110_WLAN_RAILS 6

#endif /* _PGP110_PCIE_H_ */
