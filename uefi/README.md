# pgp110（Cape / SM8475）的 UEFI 平台包：计划与清单

Mu-Silicium 的每个手机平台是一个 `Platforms/<厂商>/<代号>Pkg` 目录，加上 `Resources/` 里的
配置与设备树，再加 `Binaries/<代号>/` 里的厂商 DXE 驱动。参考机 redwood 的成品在
`devices/redwood/uefi/files/`：

```
Platforms/Xiaomi/redwoodPkg/
    redwood.dsc  redwood.dec  redwood.fdf  DeviceBuild.py
    Include/{APRIORI.inc, DXE.inc, RAW.inc}
    Library/{ConfigurationMapLib, MemoryMapLib}
Resources/Configs/redwood.toml        # fd base/size、boot image 参数
Resources/DTBs/redwood.dtb            # 平台自己的设备树
Binaries/redwood/                     # 厂商 .efi/.inf（不入库）
```

本机要做的，是同一套东西的 `pgp110` 版本。**厂商驱动已经从 `uefi_a` 分区里取出来了**
（见 `uefi-vendor/README.md`，151 个 FFS 名字 + GUID 在 `uefi-vendor/uefi-inventory.txt`）。

## 1. 已经有的输入

| 输入 | 在哪 | 状态 |
|---|---|---|
| 厂商 UEFI 固件卷 | `uefi-vendor/uefi_a.bin`（5 MB，`_FVH` @0x1000） | 已取、已解析出 165 个 FFS |
| 驱动名 + GUID | `uefi-vendor/uefi-inventory.txt` | 151 条 |
| 本机设备树 | `device-tree.dtb`（1 231 288 字节，Cape MTP） | 已取 |
| 内存保留区 | `hw-facts/iomem.txt` + 设备树 `reserved-memory` | 已取 |
| 面板配置 | `uefi_a` 里的 `Panel_oplus21605_nt37701a_1080_2412_dsc_cmd.xml` 等 10 个 | 在 FV 里，待导出 |

## 2. 要建的东西

```
devices/pgp110/uefi/
    apply.sh  export.sh                      # 照抄 redwood 的两行脚本，改名字
    files/Platforms/OnePlus/pgp110Pkg/
        pgp110.dsc  pgp110.dec  pgp110.fdf  DeviceBuild.py
        Include/{APRIORI.inc, DXE.inc, RAW.inc}
        Library/ConfigurationMapLib/  Library/MemoryMapLib/
    files/Resources/Configs/pgp110.toml
    files/Resources/DTBs/pgp110.dtb          # = device-tree.dtb
    files/Binaries/pgp110/                   # 厂商驱动，永远不入库
```

## 3. 逐项怎么填

### 3.1 `pgp110.toml`（fd 的加载地址）

redwood 是：

```toml
[uefi_fd]
base = 0x9FD00000
size = 0x200000
```

本机的线索：`abl_a` 是 32 位 ARM stub，入口 `0x9fa00000`；同代 Qualcomm 平台的 UEFI FD 常用
`0x9FD00000`。**这一项必须验证**——地址错了的表现是 `fastboot boot` 之后黑屏、无输出，手机仍在
fastboot，可以 `fastboot reboot` 回来。验证顺序：先按 `0x9FD00000/0x200000` 编，若黑屏再试
`0x9FC00000`、`0x9F800000`。

### 3.2 `MemoryMapLib`

把两份数据合起来转成表：

- 设备树 `reserved-memory`（`hyp_region@80000000`、`smem_region@80900000`、`ipa_fw_region@8b900000`、
  `mpss_region@8bc00000` …）；
- `/proc/iomem` 的 `System RAM` 段（`808f4000-808fffff`、`80d00000-856fffff`、`8b91c000-8b9fffff`、
  `a0400000-a6dfffff` …）。

redwood 的同名文件是模板，改数字不改结构。

### 3.3 `DXE.inc`（驱动清单）

按 `uefi-vendor/uefi-inventory.txt` 的 GUID 写，先只放能起屏的最小集合：

`DxeCore`、`ArmCpuDxe`、`ArmGicDxe`、`ArmTimerDxe`、`DALSys`、`DALTLMM`、`ClockDxe`、`NpaDxe`、
`I2C`、`DisplayDxe`、`GraphicsConsoleDxe`、`FontDxe`、`ButtonsDxe`、`OplusKeyDxe`、
`DiskIoDxe`、`Fat`、`FvSimpleFileSystem`、`PILDxe`、`PILProxyDxe`、`HALIOMMU`。

能起屏以后再逐个加 `IPCCDxe`、`GlinkDxe`、`ChargerExDxe`、`OGaugeAuthDxe`、`OplusVibrDxe`、`GpiDxe`、
`FeatureEnablerDxe` 等。

### 3.4 `ConfigurationMapLib`

面板名、分辨率、UART、USB 模式。面板用 `uefi_a` 里那套 `Panel_oplus21605_nt37701a_1080_2412_dsc_cmd.xml`
（与本机 DT 的 `ovaltine_boe_nt37705_1080_2412` 同代，具体一块要按 DT 的 `qcom,dsi-display-active` 定）。

### 3.5 `Binaries/pgp110/`

从 `uefi_a.bin` 里把 FFS 的 PE32 抽成 `.efi` + 生成 `.inf`（官方工具是
[UEFIReader](https://github.com/WOA-Project/UEFIReader)；`uefi_firmware` 的压缩段进程也能做）。
**这些是厂商二进制，只放本机，`tools/provenance-check.py` 会拦。**

## 4. 验收（每一步都能独立判断）

| 步 | 做什么 | 成功的样子 |
|---|---|---|
| A | `python3 build_uefi.py -d pgp110 -r RELEASE` | `Build/pgp110Pkg/RELEASE_CLANGPDB/FV/SILICIUM_UEFI.fd` 生成，≤2 MB |
| B | `fastboot boot`（由 `./xl enter` 打包） | 屏幕上出现 HakiOS 的 banner |
| C | loader 起来 | 日志里有 `== XNULOADER v3 ==`，能 `xl ramdisk` 收镜像 |

## 5. 风险

- **fd 地址错**：黑屏、无输出；手机仍在 fastboot，`fastboot reboot` 即回 Android。
- **面板序列错**：有背光无内容，或多屏闪烁。
- **内存图错**：UEFI 能起、内核起不来（卡在 `AllocatePages` 或 loader 的 payload 区）。
- **驱动 GUID 与 Mu 的期望不符**：编得过但加载时挂起，需要按 Mu-Silicium 的 `Binaries` 文档逐个对。

## 6. 现在缺的

- Mu-Silicium 源码树（`uefi/apply.sh` 会克隆，约 3 GB）与 Python 构建依赖；
- `Binaries/pgp110/` 的 PE32 导出；
- 验证 fd 地址（要真机 `fastboot boot` 一次，属于用户授权范围）。
