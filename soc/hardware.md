# 本机硬件事实（Cape / SM8475，一加 Ace Pro）

这里每一条都来自**这台手机自己**，不是从别的机型抄的。采集方式写在每节末尾，换一台机器可以原样重跑。
原始输出保留在本地工作区（厂商固件与运行期转储不进 git）。

## 0. 平台判定

| 依据 | 读数 |
|---|---|
| `/sys/devices/soc0/soc_id` | `530`（Cape / SM8475；SM8450 waipio 是 `457`） |
| `/sys/devices/soc0/machine` | `CAPE` |
| `/sys/devices/soc0/hw_platform` | `MTP` |
| 设备树 `model` / `compatible` | `Qualcomm Technologies, Inc. Cape MTP, Ovaltine` / `qcom,cape-mtp qcom,cape qcom,mtp` |
| 内存 | `MemTotal` = 15583640 kB（约 16 GB） |
| 启动设备 | `ro.boot.boot_devices` = `soc/1d84000.ufshc` |
| EGL 实现 | `ro.hardware.egl` = `adreno` |

## 1. 外设地址（`/proc/iomem` 实测，节选）

只列 HakiOS 驱动会碰的块；完整表见本地采集的 iomem 记录。

| 块 | 地址 | 说明 |
|---|---|---|
| GCC | `0x00100000` | `clock-controller cc_base` |
| GPU clock 控制器 | `0x03d90000`–`0x03d99fff` | `3d90000.clock-controller`（GPUCC） |
| GPU SMMU | `0x03da0000`–`0x03ddffff` | `3da0000.kgsl-smmu base`；TCU 在 `0x03de6000` |
| GPU TBU | `0x03de9000` / `0x03ded000` | `gfx_0_tbu` / `gfx_1_tbu` |
| Apps SMMU | `0x15000000`–`0x150fffff` | `apps-smmu base`，TCU `0x151ce000` |
| UFS PHY | `0x01d80000`–`0x01d81fff` | `ufsphy_mem` |
| UFS 控制器 | `0x01d84000`–`0x01d86fff` | `ufshc ufs_mem` |
| UFS ICE | `0x01d88000` / `0x01d90000` | `ufs_ice` / `ufs_ice_hwkm` |
| IPCC | `0x0ed18000`–`0x0ed18fff` | `qcom,ipcc@ed18000` |
| PCIe | `0x60200000`–`0x63ffffff` | `qcom,pcie@1c00000` |
| 显示时钟 | `0x0af00000`–`0x0af1ffff` | `clock-controller@af00000`（DISPCC） |
| 温感 | `0x0c263000` / `0x0c265000` | `thermal-sensor@c263000` / `@c265000` |
| Pinctrl | `0x0f000000`–`0x0fffffff` | `pinctrl@f000000` |
| QUPv3 | `0x009c0000` 等 | `qupv3_0/1/2_geni_se` |
| SP 协处理器 | `0x188101c` 起 | `remoteproc-spss`（安全处理器） |

**注意 `0x3d00000`（3D 核心）和 `0xae00000`（MDP）没有出现在 `/proc/iomem` 里**——kgsl 与 SDE
用 `ioremap` 而不申请 region，所以这两个地址只能从设备树取（`kgsl-3d0@3d00000`、
`mdss_mdp@ae00000`），不要因为 iomem 里没有就以为不存在。

内存保留区（`System RAM` 之外的部分，与设备树 `reserved-memory` 对得上）：

```
80000000-808f3fff reserved        80900000-80cfffff reserved
85700000-8b91bfff reserved        8ba00000-a03fffff reserved
a0400000-a6dfffff System RAM
```

## 2. 电源芯片（PMIC）

热区名字直接暴露了本机的 PMIC 组合，这是移植调压器/充电时必查的一组：

`pm8350`、`pm8350b`、`pm8350c`、`pmr735a`、`pmr735b`、`pm8450`、`pm8010i`、`pm8010j`

对应的热区：`pm8350_tz`、`pm8350c_tz`、`pm8350c-bcl-lvl0/1/2`、`pm8350b_tz`、
`pm8350b-ibat-lvl0/1`、`pm8350b-bcl-lvl0/1/2`、`pmr735a_tz`、`pmr735b_tz`、`pm8450_tz`、
`pm8010i_tz`、`pm8010j_tz`。

## 3. 温度区（`/sys/class/thermal/thermal_zone*/type`）

一共 70+ 个，命名分两类：

- **SoC 内部**：`aoss-0/1`、`cpuss-0..3`、`cpu-0-*` / `cpu-1-*`（每核一个）、`gpuss-0/1`（GPU）、
  `nspss-0..2`（NPU）、`mdmss-0..3`（调制解调器）、`camera-0/1`、`video`、`ddr`、`isense_trim`；
- **板级/PMIC**：`pm8350*`、`pmr735*`、`pm8450_tz`、`skin-msm-therm`、`conn-therm`、`xo-therm`、
  `rear-cam-therm`、`wlc-therm`、`battery`、`usb`、`shell_front/frame/back`。

HakiOS 的 `thermal=1` 要读的是 `aoss-0`/`cpuss-0`/`gpuss-0` 这一组。本机有两个 tsens 块，都是
`qcom,tsens-v2`、各 16 个传感器：

| 节点 | `reg` | 中断 |
|---|---|---|
| `/soc/thermal-sensor@c263000` | `0xc263000`（长度 `0x1ff`）+ `0xc222000` | 506（uplow）、508（critical） |
| `/soc/thermal-sensor@c265000` | `0xc265000`（长度 `0x1ff`）+ `0xc223000` | 507（uplow）、509（critical） |

参考驱动（`hakios.adreno.c:3549`）把 `tsens1` 定在 `0x0c265000`。本机两个块都在，但
“哪个块对应内核的 tsens0/tsens1、第几个传感器对应 `gpuss-0`”必须按设备树把它们挂到
`thermal-zones` 的顺序核对（`thermal-sensors = <&phandle N>`），不能照抄参考机的编号。

## 4. 显示

| 项 | 值 |
|---|---|
| MDP | `qcom,mdss_mdp@ae00000`（`qcom,sde-*` 属性一整页，DPU 版本要按 `qcom,sde-highest-bank-bit` 等推断） |
| 面板 | `/soc/dsi_oplus_ovaltine_boe_nt37705_1080_2412_dsc_cmd`（`qcom,dsi-display-active` 标出本机在用哪一块） |
| 分辨率 | 1080 × 2412，`dsc_cmd`（DSC 压缩命令模式） |
| 背光 | `bl_ctrl_dcs`（`qcom,mdss-dsi-bl-pmic-control-type`） |
| 面板电源 | `vddio`（1.8 V）/ `vddr`（1.2 V 档，`qcom,panel_voltage_vddr` 给的是三档值） |

这块面板是 OPPO 定制的 `cmd` 模式 + DSC + ADFR，初始化序列在设备树里（`qcom,mdss-dsi-on-command`
等属性）。HakiOS 的显示驱动要先能发这套 DCS 序列，屏幕才会亮；这比“把 framebuffer 指过去”难得多。

## 5. 存储

`ufshc@1d84000`，`qcom,ufshc`，时钟表 `freq-table-hz` 里 `core_clk` 从 `0x47868c0`（75 MHz）
到 `0x32a9f880`（850 MHz）；`dma-coherent`；有 ICE（内联加密）。

> `ro.boot.boot_devices` 指向它，说明 HakiOS 的 UFS 驱动要按这颗控制器的寄存器表来，参考机的表只能当模板。

## 6. 采集命令（换机器可复用）

```sh
# 平台
adb shell su -c 'cat /sys/devices/soc0/{soc_id,machine,hw_platform}'
# 设备树（二进制，用 exec-out 直出）
adb exec-out su -c 'cat /sys/firmware/fdt' > device-tree.dtb
# 外设地址
adb shell su -c 'cat /proc/iomem'
# 温度区
adb shell su -c 'cat /sys/class/thermal/thermal_zone*/type'
# 中断
adb shell su -c 'cat /proc/interrupts'
```

## 7. 取不到的（本机限制，如实记）

| 想取 | 结果 |
|---|---|
| `/sys/kernel/debug/clk/clk_summary` | 文件不存在（debugfs 没挂） |
| `/sys/kernel/debug/regulator/regulator_summary` | 同上 |
| `dmesg`（即使 root） | `klogctl: Permission denied`——本 ROM 的 `su` 域没有 syslog 权限 |
| `/vendor/firmware_mnt/image` 列表 | SELinux 拒绝（`u:r:su:s0`）；固件改从 `/vendor/firmware` 取 |

所以**时钟树与调压器表要从设备树补**（`clock-controller` / `regulator-*` 节点都在树里），
而不是等 debugfs。这反而更适合移植：设备树就是内核要读的那份。
