# Hackios-trao

**HakiOS 设备层仓库 —— 一加 Ace Pro（PGP110）/ 一加 10T（AQ101，全球版），高通 Cape / SM8475。**

本仓库只存放这台机器的**设备适配层**：设备配置、SoC 硬件事实、UEFI 平台包源码、移植脚本与设备树事实。HakiOS 的公共内核、loader 与通用驱动在公共仓库中，按 HakiOS 官方「一设备一仓库」的格式组织，本仓库是其中的 `pgp110` 设备仓库。

> 这是一个**研究性移植**，尚未在真机上完成一次可引导启动。下表每一项都标注了当前可用性与证据边界，请先阅读「现状与可用性」再使用。

## 支持机型

| 市场名 | 代号 | 地区 | 备注 |
|---|---|---|---|
| OnePlus Ace Pro | PGP110 | 中国大陆 | 本仓库全部事实来自一台 PGP110 实机 |
| OnePlus 10T | AQ101 | 全球版 | 同一 Cape / SM8475 硬件；参数与设备树需在 AQ101 实机上重新核对 |

### 硬件概要（来自本机设备树与 `/proc/iomem` 实测）

| 项 | 值 |
|---|---|
| SoC | Qualcomm Snapdragon 8+ Gen 1，Cape / SM8475（`soc_id` 530，machine `CAPE`） |
| CPU | 8 核（时钟树与拓扑未移植） |
| GPU | Adreno 730，gen7-4-0（`qcom,chipid 0x7030002`） |
| 内存 | 16 GB（`MemTotal` 15 583 640 kB） |
| 存储 | UFS，`ufshc@1d84000` |
| 显示 | 1080 × 2412，DSC 命令模式，面板 `ovaltine_boe_nt37705` |
| 触摸 | Synaptics S3910，SE4  SPI（gpio16/17/18/19），INT gpio21，RESET gpio20，1.8 V 使能 gpio97 |
| Wi-Fi | Qualcomm QCA6490，PCIe0 / MHI |
| PMIC | pm8350 / pm8350b / pm8350c、pmr735a / pmr735b、pm8450、pm8010i / pm8010j |

## 现状与可用性

状态口径：**works** 真机可用；**partial** 有部分进展或单次实验证据，但未稳定可用；**missing** 未开始或仅有事实采集。证据与缺口详见 `soc/`、`uefi/STATUS.md` 与 `device.conf`。

| 子系统 | 状态 | 当前进展与未完成项 |
|---|---|---|
| UEFI 平台包 | partial | Mu-Silicium 平台包骨架可被工具链解析；在补入本机厂商 RawFiles 的本地构建中曾产出 FD 镜像（49 个镜像校验通过）。真机 `fastboot boot` 无日志输出、停在厂商标识。`MemoryMapLib` / `ConfigurationMapLib` 仍带参考机数字，FD 加载地址未在真机验证。 |
| 内核 SoC 层 | partial | 设备 defconfig / 配置片段已写好；当前快照仅启用 UFS 驱动；其余公共驱动在本设备配置中关闭，寄存器表未按本机设备树逐项核对。 |
| 启动链（BootShim → UEFI → XNU） | missing | 真机尚未完成一次可引导启动。 |
| 显示 | partial | 单次启动实验中观察到 1080 × 2412 帧缓冲；SDE/DSI 面板驱动与 DCS 初始化序列未移植。 |
| 触摸（S3910） | partial | 驱动移植配方与接线已备好（见 `tools/port-s3910-pgp110.py`）；卡在 PMIC arbiter v7 命令编码与电源轨，SPI 读到 0 字节。 |
| 按键 | missing | 本机引脚映射尚未读取。 |
| CPU | missing | 时钟与 8 核拓扑未移植。 |
| GPU（Adreno 730） | partial | 单次启动中 18 步上电序列通过：GMU 固件加载、zap shader 鉴权、3D 核心写内存、HakiosGPU 服务起来；Mesa 渲染与 UI 加速未做。 |
| 存储（UFS） | missing | `ufshc@1d84000` 寄存器表未核对；参考机驱动仅作模板。 |
| Wi-Fi（QCA6490） | partial | PCIe0 / MHI 的地址、引脚、电源轨事实已采集（`soc/wifi.md`、`soc/wifi/pgp110-pcie.h`、`configs/pgp110-wifi-sm8475.json`）；PCIe/MHI 驱动未写，DMA/MSI 未测。 |
| 蓝牙 | missing | 未开始。 |
| 音频 | missing | ADSP 固件与 codec 未移植。 |
| 电池 | missing | 电量经 ADSP 上报，未移植。 |
| 马达 | missing | 未尝试。 |
| 相机 | missing | 未尝试。 |
| 蜂窝 | missing | 调制解调器固件未拉取；IPA 布局与参考机不同。 |
| 温控 | missing | 温区存在，尚无驱动读取。 |

### 本地实验（不在本仓库、不可由本仓库复现）

- 单次实验中 Darwin 用户态解包、APFS 镜像本地构建，一度到达 launchd。Apple IPSW 与用户态镜像属于 Apple 资产，不在本仓库内分发。
- GPU / 触摸的单次启动证据来自本地 WSL 完整工作树；本仓库仅保留移植配方脚本与事实文档，不含对应驱动二进制或实验日志。

## 仓库结构

```
Hackios-trao/
├── device.conf                      # 设备身份与各子系统可用性（hakios-device.py 读取）
├── soc.args                        # SoC 地址 / PAS / IPA 等启动参数事实
├── pull-firmware.sh                # 从本机 Android 拉取厂商固件到本地 fw-*（不入库）
├── configs/
│   ├── pgp110_defconfig            # defconfig：公共 + sm8475 + 本设备片段
│   ├── pgp110.config               # 本设备驱动开关片段
│   └── pgp110-wifi-sm8475.json     # Wi-Fi / PCIe0 事实表（本机设备树 + Android 日志）
├── soc/
│   ├── soc.conf
│   ├── configs/sm8475.config
│   ├── hardware.md                  # 本机外设地址、PMIC、温区、显示、存储事实
│   ├── gpu.md                      # Adreno 730 寄存器块、固件与移植清单
│   ├── wifi.md                      # QCA6490 / PCIe0 / MHI 事实与对接方案
│   └── wifi/pgp110-pcie.h           # 由事实生成的 C 头文件
├── uefi/
│   ├── README.md                    # UEFI 平台包计划与清单
│   ├── STATUS.md                    # 平台包编译与真机测试审计记录
│   └── files/
│       ├── Platforms/OnePlus/pgp110Pkg/   # Mu-Silicium 平台包源码（dsc/dec/fdf/源码/库/测试）
│       ├── Resources/Configs/pgp110.toml  # FD 基址/大小、boot image 参数
│       ├── Resources/DTBs/pgp110.dtb      # 本机设备树
│       └── Binaries/pgp110/README.md     # 厂商二进制说明（二进制本身不入库）
├── prebuilt/
│   ├── BootShim.bin                # BootShim 占位（构建期由 Mu BootShim 源码编译）
│   ├── device-tree.dtb             # 本机设备树事实
│   ├── mkbootimg.py                 # AOSP boot image 打包工具（Apache-2.0）
│   └── ramdisk                     # 占位 ramdisk
└── tools/                          # 移植与探查脚本（在完整 HakiOS 工作树中使用）
```

## 构建

本仓库是设备层，不能单独编出可引导镜像；需要配合完整的 HakiOS 公共源码树。

### 内核配置

```sh
# 在完整 HakiOS 工作树中，将本仓库放到 devices/pgp110/
make pgp110_defconfig
# 按公共仓库文档构建内核：
make kernel DEVICE=pgp110
```

### UEFI 平台包

平台包源码位于 `uefi/files/Platforms/OnePlus/pgp110Pkg/`，在 Mu-Silicium 源码树中按公共构建脚本编译；厂商 DXE 与面板 RawFiles 需从**你自己的手机固件**本地提取（见 `uefi/files/Binaries/pgp110/README.md`），本仓库不提供这些二进制。

### 拉取本机固件（本地、不入库）

```sh
# 手机连接 adb、处于 Android；固件落到工作树 fw-wifi/、fw-gpu/，由 .gitignore 排除
./pull-firmware.sh
```

## 不在本仓库的内容（来源边界）

- **厂商 UEFI 二进制**：`uefi_a` 分区提取的 DXE `.efi` / `.inf` 与面板 RawFiles，Qualcomm / OnePlus 所有。
- **设备固件**：GPU（`gmu_gen70000.bin`、`a730_sqe.fw`、`a730_zap.*`）、Wi-Fi（`amss20.bin`、`amss.bin`、`m3.bin`、`regdb.bin`、`bdwlang.b0c`）、音频 DSP、调制解调器、马达、相机固件。
- **Apple 资产**：IPSW、Darwin 用户态镜像、dyld 缓存、cryptex、SDK。
- **运行期产物**：日志、内存转储、快照、备份镜像、APFS 镜像、实验数据。

以上内容由每位使用者从**自己的设备与固件**取得，本仓库不分发、不内嵌其副本。

## 二进制与事实来源

| 文件 | 来源 | 处置 |
|---|---|---|
| `prebuilt/device-tree.dtb`、两份 DTB 副本 | 本机 `/sys/firmware/fdt` 采集 | 硬件事实，待核对；作为构建输入保留 |
| `prebuilt/BootShim.bin` | Mu BootShim 源码构建 | 开源构建产物，占位副本 |
| `prebuilt/mkbootimg.py` | Android Open Source Project | Apache-2.0，未改动上游工具 |
| UEFI 平台包源码 | Project Mu / Mu-Silicium 派生 | BSD-2-Clause-Patent，文件头标注 |

## 许可证

本仓库自有代码（设备配置、SoC 事实、平台包源码、脚本、文档）以 MIT 许可证发布；第三方组件及其许可证见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。设备固件、Apple 操作系统与商标不属于本仓库，亦不由本仓库授权。

## 免责声明

研究性移植，按「现状」提供，不作任何可用性担保。任何真机启动操作前，必须先审计镜像副作用、核验产物哈希与日志保留路径；未经审计不要刷写分区，固件一律走 RAM 启动（`fastboot boot`）。风险由操作者自行承担。
