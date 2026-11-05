# 本机 Wi-Fi：QCA6490 on PCIe0

每条都来自这台手机自己：设备树（`/sys/firmware/fdt`）、Android 内核日志（2026-11-05 抓取）、
运行时 `/sys`。完整分析记录保留在本地工作区，不随本仓库分发。

## 1. 芯片与总线

| 项 | 值 | 证据 |
|---|---|---|
| 芯片 | **QCA6490**（WCN6855 家族，Wi-Fi 6E 2×2） | DT `compatible = "qcom,cnss-qca6490"`；日志 `qca6490:` |
| PCI | `0x17cb:0x1103`，class `0x028000` | 日志与 `/sys/bus/pci` |
| 总线 | PCIe0（`qcom,pcie@1c00000`），Gen2 ×1 | 日志 `link initialized`、`speed 0x2 / width 0x1` |
| BAR0 | `0x60200000` + `0x200000` | 日志 `BAR 0: [mem 0x60200000-0x603fffff]` |
| DMA | IOVA `0xa0000000` + `0x10000000`，36 位 | 日志 `iova ... size 0x10010000`、`DMA MASK 0xfffffffff` |
| SMMU | Apps SMMU `0x15000000`，WLAN **SID `0x1c01`** | DT `iommu-map` |
| 中断 | int_global_int = SPI140 → GIC INTID 172 | DT `interrupt-map` |
| MHI | 3 MSI（base 0）+ WAKE（data 13） | 日志 `Assign MSI to user` |
| 工程号 | 21841 | 日志 + DT |

## 2. 地址

| 块 | 地址 | DT |
|---|---|---|
| PARF | `0x1c00000`–`0x1c02fff` | `reg-names = "parf"` |
| PHY | `0x1c06000`–`0x1c07fff` | `"phy"` |
| DM core | `0x60000000` | `"dm_core"` |
| ELBI | `0x60000f20` | `"elbi"` |
| IATU | `0x60001000` | `"iatu"` |
| CFG | `0x60100000` | `"conf"` |
| BAR0 | `0x60200000` | Linux 分配的 BAR |
| GCC | `0x100000` | `clock-controller@100000` |
| GDSC | `0x17b004`（collapse vote `0x162128` bit0） | `qcom,gdsc@17b004` |
| TLMM | `0xf100000` | `pinctrl@f000000` |
| PMIC arbiter | cnfg `0xc42d000` / core `0xc400000` / obsrvr `0xc440000`（**v7**） | `qcom,spmi@c42d000` |
| RPMh RSC | `0x17a00000`，drv2 `0x17a20000`，TCS offset `0xd00` | `rsc@17a00000` |
| cmd-db | `0x80860000` + `0x20000` | `aop_cmd_db_region@80860000` |

## 3. 引脚与供电

| 用途 | GPIO / 轨 |
|---|---|
| WLAN 使能 | `gpio80`（拉高 ≥2 ms） |
| BT 使能 | `gpio81` |
| SW ctrl | `gpio82` |
| XO 时钟 | `gpio204`（EN 后 2–5 ms 内撤销） |
| PERST# | `gpio94` |
| CLKREQ# | `gpio95`（`pcie0_clkreqn`） |
| WAKE# | `gpio96` |
| 供电 | `vdd-wlan-io pm8350_s10`、`vdd-wlan-aon pmr735a_s2`、`vdd-wlan-dig pm8350_s11`、`vdd-wlan-rfa1 pm8350c_s1`、`vdd-wlan-rfa2 pm8350_s12`、`ant pmr735a_l7` |

`gpio204` 在 TLMM 上归 LPASS/SSC 所有：要写 `CFG` 的 bit12（EGPIO claim），只改 `[9:0]` 的功能位；
Pong 的 `pin()` 是这种做法，已实机验证。

## 4. 固件（`fw-wifi/qca6490/`，`pull-firmware.sh` 从 Android 只读取出）

| 文件 | 用途 |
|---|---|
| `amss20.bin` | 本机实际固件（hw major 0x12） |
| `amss.bin` | hw1 备用 |
| `m3.bin` | M3 引导 |
| `bdwlang.b0c` | BDF（region 1 / project 21841，来自 `/odm/etc/wifi/qca6490/`） |
| `regdb.bin` | 法规库 |

`Data.msc`/`Data20.msc`（校准库）本机 `CalDB: 0`，不需要。**固件不入 git。**

## 5. 上电到联网（Android 日志 2.1–6.9 s，详见报告第 3 节）

```
cnss probe → 六路 rail → WLAN_EN → PERST# 释放 → 链路训练 → 枚举 17cb:1103
→ SMMU/IOVA → MHI 3 向量 → amss20 下载 → MISSION_MODE → link Gen2
→ WLFW server(QRTR node7 port1) → 主机能力 → FW 内存请求 → regdb → bdwlang.b0c
→ m3 → FW ready → CALIBRATION → pin connect → cnss-daemon
```

## 6. 和 HakiOS 现有 Wi-Fi 栈的关系

现有 `drivers/wifi/` + `wifi/lx` 是 **WCN6750（AHB + WPSS）** 的路径：
AHB 窗口、GLINK/QRTR、TrustZone 启动 WPSS。QCA6490 是 **PCIe + MHI + QRTR-MHI**，
需要新增 PCIe RC/PHY/MHI 传输；上半部分（station、WPA、Apple80211、mac80211 等价层）可直接复用。

参考：同芯片、同 SoC 的 PongWifi 驱动（已实机连网）与
`Ath12kWifi`（Linux 7.0.14 的 MHI/QRTR/QMI 传输）。

## 7. 采集方式

```powershell
# 设备树
adb shell su -c "dd if=/sys/firmware/fdt of=/sdcard/fdt.bin bs=4096"
adb pull /sdcard/fdt.bin
wsl -e bash -lc 'dtc -I dtb -O dts -o fdt.dts fdt.bin'

# 固件（在完整 HakiOS 工作树中执行）
bash devices/pgp110/pull-firmware.sh

# 日志（OPPO logkit 的 @wifi 抓取）
adb pull /sdcard/Android/data/com.oplus.logkit/files/Log/<时间>@wifi
```
