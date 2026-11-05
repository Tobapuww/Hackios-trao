# GPU：Adreno 730（Cape / SM8475）在 HakiOS 里的移植笔记

结论先说：**这台机器的 GPU 不是把 `gpu=1` 打开就能用。** 仓库里的 `drivers/gpu/hakios.adreno.c`
是给参考机 redwood 的 **Adreno 642L（a660，第六代）** 写的：寄存器块、GMU 固件名、HFI 协议、
电源时序都按那一颗取了具体数字。Adreno 730 是 **gen7-4-0（第七代）**，固件名与寄存器布局都不同。
下表是从**本机自己的设备树**和 `/vendor/firmware` 取到的实测数据，以及需要改的地方。

## 一、本机实测

设备树节点：`/soc/qcom,kgsl-3d0@3d00000`

| 属性 | 值 |
|---|---|
| `compatible` | `qcom,adreno-gpu-gen7-4-0`、`qcom,kgsl-3d0` |
| `qcom,gpu-model` | `Adreno730v3` |
| `qcom,chipid` | `0x7030002` |
| `qcom,ubwc-mode` | `0x4` |
| `interrupts` | `<0 0x12c 4>`（kgsl_3d0_irq）、`<0 0x11e 4>`（freq_limiter_irq） |
| `qcom,tzone-names` | `gpuss-0`、`gpuss-1`（温度区，`/soc/thermal-zones/gpuss-*`） |
| `qcom,gpu-qdss-stm` | `0x161c0000`，长 `0x40000` |
| `qcom,initial-pwrlevel` | `0xb` |

`reg` / `reg-names`（7 段）：

| 名字 | 基址 | 长度 |
|---|---|---|
| `kgsl_3d0_reg_memory` | `0x3d00000` | `0x40000` |
| `cx_dbgc` | `0x3d61000` | `0x800` |
| `rscc` | `0x3d50000` | `0x10000` |
| `isense_cntl` | `0x3d8b000` | `0x2000` |
| `cx_misc` | `0x3d9e000` | `0x1000` |
| `qdss_gfx` | `0x10900000` | `0x80000` |
| `rdpm_cx` | `0x634000` | `0x1000` |

Zap 着色器：`kgsl-3d0/zap-shader` 的 `memory-region` 指向
`reserved-memory/gpu_microcode_region@8b91a000`（`0x2000` 字节，`no-map`）。
也就是说固件由 bootloader/内核预留在 `0x8b91a000`，不是由 GPU 驱动自己去分配。

从本机 `/vendor/firmware` 取出的固件（已放在工作区 `fw-gpu/`，共 8 个文件、166 KB）：

| 文件 | 大小 | 作用 |
|---|---|---|
| `gmu_gen70000.bin` | 57272 | **GMU 固件**。第七代的命名是 `gmu_gen70000.bin`，不是 `a660_gmu.bin` |
| `a730_sqe.fw` | 75924 | 3D 核心的微码（SQE） |
| `a730_zap.mdt` | 3564 | Zap 着色器的头（含段表与哈希） |
| `a730_zap.b00` / `.b01` / `.b02` | 148 / 2236 / 3416 | Zap 着色器的段 |
| `a730_zap.elf` / `.mbn` | 11608 / 12088 | 同一份 Zap 的可执行/签名形式 |

取法：固件在 `/vendor/firmware`，`su` 下 `cp` 到 `/sdcard`，再 `adb pull`。
`/vendor/firmware_mnt/image` 在 `u:r:su:s0` 下连 `ls` 都会被 SELinux 拒绝，别从那取。

## 二、和参考驱动的差异

| 项 | 参考机（redwood，a660） | 本机（Cape，a730） |
|---|---|---|
| 3D 核心 | `0x3d00000`，长 `0x40000` | `0x3d00000`，长 `0x40000`（同） |
| GMU | `0x3d6a000`，长 `0x34000`（`hakios.adreno.c:890`） | 设备树里没有独立的 GMU 节点，GMU 在 `kgsl_3d0` 区内/由 `qcom,gmu` 描述，需按本机树重算 |
| RSCC | `0x3de0000`（`:976`） | **`0x3d50000`，长 `0x10000`**（差 `0x90000`） |
| cx_misc | `0x3d9e000` | `0x3d9e000`（同） |
| GPUCC | `0x3d90000`，长 `0x9000` | 需从本机 `clock-controller` 节点重取 |
| SMMU | `0x3da0000`，长 `0x20000` | 需按本机 `apps-smmu`/GPU SMMU 节点重取 |
| PDC | `0xb290000`（`:2000`） | 需按本机树重取 |
| GMU 固件 | `a660_gmu.bin`（`:1747`） | **`gmu_gen70000.bin`** |
| SQE 微码 | `a660_sqe.fw`（`:2570`） | **`a730_sqe.fw`** |
| Zap 头/段 | `a660_zap.mdt`、`a660_zap.b02`（`:1651`、`:2654`） | **`a730_zap.mdt`、`a730_zap.b02`**，且 `no-map` 区在 `0x8b91a000` |
| HFI 协议 | 第六代 GMU 的消息集 | 第七代换了一代：消息号、`HFI_*` 表、`GMU_*` 寄存器偏移都要按 `gen7` 重做 |
| 中断号 | 参考机自己的 | `300`（3D core）、`286`（freq limiter） |

这些数字都是从本机树里读出来的（`tools/dt-node.py` 就是为读它写的），不是猜的；
而**寄存器偏移**（`RSCC_*`、`GMU_*`、`CX_MISC_*` 那些 `#define`）是从
`a6xx_gmu.xml` 抄的，第七代要换一张表——这是最花时间的部分。

## 三、要改的清单（按依赖顺序）

1. **寄存器块**：把 `hakios.adreno.c` 里的 `struct block` 改成从本机设备树的 `reg`/`reg-names` 读，
   或者按上表写死。目标是先把 `gpucc`/`rscc`/`cx_misc` 点亮、读到 `qcom,chipid`。
2. **时钟与电源**：GPUCC 的时钟树、`cx`/`gx` 两条电源轨、`rscc` 的 RSC 命令槽（这台机器上 RSCC 换了地址，
   槽表也要按 gen7 的 `a6xx_rscc` 等价物重写）。
3. **GMU 启动**：用 `gmu_gen70000.bin` 走 GMU 的 bootloader → HFI 固件加载 → `HFI_GMU_BOOT` 这条链。
   参考实现可以对着 Mesa 的 `freedreno`（`a6xx_gmu.c` / `a7xx` 补丁）与 Android 的 `kgsl`
   的 `a730` 代码翻译，但不能照抄 a660 的偏移。
4. **SMMU/IOMMU**：GPU 的 TTBR、上下文库、`gpu_microcode_region` 的映射；UBWC 配置按 `qcom,ubwc-mode = 4`。
5. **Zap**：把 `a730_zap.*` 送进 TZ（PAS id 与 secure 侧的约定），拿到 RBBM 的访问许可。
6. **3D 核心**：RBBM/CP/`SQE` 微码、ring、`isense`、`rdpm` 计数器；这一步之后才是“能画一个三角形”。
7. **Mesa 用户态**：本项目的 OpenGL ES 走 Mesa（`gpu=1` + `GL=1` 的镜像）。a7xx 在 Mesa 里是
   较新的后端，内核侧接口对齐之后，用户态的 `fd` 后端也要用 a730 的 `chip_id` 走对分支。
8. **验收**：
   - 阶段 A：`gpu=1` 启动后日志里出现 GMU 起来、`chipid=0x7030002`、时钟/电源轨读数正常；
   - 阶段 B：Zap 通过、SMMU 有域、ring 能提交一个 `NOP`；
   - 阶段 C：Mesa 探测到 `a730`，`glClear` 出一帧（屏幕上出现纯色），日志无 GPU fault；
   - 阶段 D：主屏渲染（这一步依赖显示驱动先通）。

## 四、为什么“先点亮开机界面”比 GPU 更靠前

开机界面（Apple 标志/锁屏）要的是：UEFI 的 framebuffer → loader → XNU 起来 → 显示驱动（SDE/DSI）
→ 合成器。GPU 只负责“画得快”，没有它系统仍然能用软件合成出界面。所以真实的顺序是：

1. UEFI（Cape 平台）——现在没有，最重；
2. 内核 SoC 层 + 显示（SDE/DSI/面板）——能出画面；
3. 用户态 16.5（你自己的 IPSW）；
4. GPU（本文档）。

也就是说：**GPU 驱动不可能先于“能开机”完成**，它依赖内核已经在跑、时钟/电源框架已经工作。
