# pgp110 的 UEFI：从 redwood 平台改名/改驱动而来（第二轮）

> **2026-11-02 用户更正与证据限定（优先于下文历史推断）**
> - 实际设备是 **PGP110**；PMA110 是当前移植系统的来源，不是实际设备型号。下文 Ace Pro 等生成配置不构成硬件身份依据。
> - 当前用户可见现象：`fastboot boot` 无法启动目标镜像，**没有任何日志或输出，只显示厂商标识**。未取得本次 PC 端原始输出，不能假定已返回 `Booting OKAY`。
> - 下文“镜像被执行，UEFI 卡在内部”“卡点在存储栈之前”“UEFI 没走到能写日志的地方”均是未证实推断；没有日志文件不能单独定位故障阶段。历史轮次结果保留，不视作本次重测。
> - 本轮仅检查本地文档和源码，未执行设备启动、重启、清分区或刷写。

这份是**用脚本生成的骨架**，不是手写完成品。生成器：`tools/make-pgp110-uefi.py`。

## 已做的机械变换

| 步骤 | 结果 |
|---|---|
| 复制 `devices/redwood/uefi/files/Platforms/Xiaomi/redwoodPkg` | → `Platforms/OnePlus/pgp110Pkg` |
| 改名 | `redwood.dsc/.dec/.fdf` → `pgp110.*`，`redwoodPkg` → `pgp110Pkg` |
| 路径 | `Binaries/redwood/` → `Binaries/pgp110/` |
| SMBIOS | 厂商 `Xiaomi` → `OnePlus`，机型 `POCO_X5_Pro_5G_redwood` → `Ace_Pro_pgp110` |
| ACPI | `lisa/AcpiTables.inf` 整行注释掉（cape 的 ACPI 表还没有，见下） |
| 驱动清单 | `Include/DXE.inc`、`Include/APRIORI.inc` 里每条 `Binaries/.../<Name>.inf` 都换成**本机 uefi_a 里真实存在的驱动名** |
| RAW 文件 | `Include/RAW.inc` 由本机固件卷重新生成（64 个，见下） |
| 资源 | `Resources/Configs/pgp110.toml`、`Resources/DTBs/pgp110.dtb`（= 本机设备树） |

驱动名的对应表（redwood 名 → 本机名）写在生成器的 `SPECIAL` 里，逐个核对过：

```
ChipInfoDxe→ChipInfo   DALSYSDxe→DALSys   HALIOMMUDxe→HALIOMMU
HWIODxe→HWIODxeDriver  I2CDxe→I2C         PlatformInfoDxe→PlatformInfoDxeDriver
ProjectInfoDxe→OplusProject  TLMMDxe→DALTLMM  SPIDxe→SPI  SPMIDxe→SPMI
TzDxe→TzDxeLA  ScmDxe→ScmDxeLA  XhciPciEmulationDxe→XhciPciEmulation
QcomChargerDxe→QcomChargerDxeLA  GLinkDxe→GlinkDxe
```

没有对应物的只有 `RNGDxe`（已在清单里注释掉）。

## 厂商二进制（不入库，本机放在 `uefi-vendor/`）

```
uefi-vendor/Binaries-pgp110-Mu/pgp110/
    QcomPkg/Drivers/<Name>/<Name>.inf + <Name>.efi     # 84 个
    RawFiles/<name>                                     # 64 个：面板 XML、SecParti.cfg、
                                                        #  uefipil.cfg、QcomChargerCfg.cfg、
                                                        #  PanelSimConfig.csv、BDS_Menu.cfg…
```

`.inf` 是标准 binary INF（`PE32|<name>.efi|TRUE`），FILE_GUID 用固件卷里 FFS 的真实 GUID。
RawFiles 的名字取自 UEFI 的 UI section（**UCS-2 编码**，按 UTF-16-LE 解）。

## 编译到哪一步了

```
python3 build_uefi.py -d pgp110 -r RELEASE
```

| 轮次 | 结果 |
|---|---|
| 第 1 次（redwood 对照） | EDK2 环境起来；只差 `Binaries/redwood/...`（厂商件不入库）→ **工具链可用** |
| 第 2 次（pgp110） | 报缺 `Binaries/pgp110/RawFiles/SecParti.cfg` |
| 第 3 次（补 RawFiles 后） | 过了解析 RAW，停在 FDF 的 `INF QcomPkg/Applications/MassStorage/MassStorage.inf`（FDF 解析层） |

也就是：**平台包能被识别、驱动清单能对上、RAW 能展开；剩下的错误在 FDF 语句层**。

### 第 4–6 次：三个真实错误，逐个修掉后**编译成功**

| 轮次 | 错误 | 原因 | 修法 |
|---|---|---|---|
| 4 | `INF RuleOverride = ACPITABLE` 处 FDF 解析失败 | 生成器只把 `lisa/AcpiTables.inf` 换成注释，留下半条语句 | 正则整行注释掉 |
| 5 | OverrideValidation：`lisa/AcpiTables.inf` 转绝对路径失败 | `.dsc` 的 `[Components]` 里还留着它 | 生成器把 `.dsc` 里该行也注释掉 |
| 6 | GenFv：`the 11th file and 12th file have the same file GUID` | 映射按**目录名**取模块，`TzDxe/ScmDxeLA.inf` 和 `TzDxe/TzDxeLA.inf` 都被映射成 `TzDxeLA` | 改为按**文件名**映射 |

结果：

```
- Done -
FV Space Information
FVMAIN [99%Full] 6868992 total, 6867152 used
FVMAIN_COMPACT [51%Full] 2097152 total, 1088576 used
0048 Images Verified
Success

Build/pgp110Pkg/RELEASE_CLANGPDB/FV/SILICIUM_UEFI.fd   2 097 152 字节（= 0x200000，与 toml 一致）
```

已复制到 `uefi-vendor/pgp110-build/SILICIUM_UEFI.fd`。**这是这套移植第一次产出可引导格式的 UEFI 固件镜像**
（尚未在真机上 `fastboot boot` 验证）。

## 仍未做（如实）

1. **MemoryMapLib / ConfigurationMapLib 还是 redwood 的数字**——直接刷会按 778G 的内存图跑，必须按
   `hw-facts/iomem.txt` + 本机设备的 `reserved-memory` 重写；
2. **ACPI 表没有**：已从 `.dsc`/`.fdf` 里去掉（XNU 不依赖 ACPI，UEFI 侧要用时再补）；
3. **fd 加载地址**仍沿用 `0x9FD00000/0x200000`（红木的值），必须在真机上验证；
4. 面板 XML 里哪一块是这台机器的（DT 的 `qcom,dsi-display-active` 指向 `ovaltine_boe_nt37705`）；
5. FVMAIN 已 **99% 满**：再加驱动会放不下，下一步要么精简（去掉用不到的驱动），要么放大 FV（受 fd 大小限制）。

---

## 真机测试记录（2026-11-02）

| 轮次 | 镜像 | 结果 |
|---|---|---|
| 1 | header **v1**，FD `0x9FD00000/2MB`，SC7280 内存图 | `Booting OKAY` 后 0.35 s 回 fastboot → **v1 被 ABL 丢弃** |
| — | **原厂 `boot_a.img`（v4）** | `fastboot boot` 成功，adb 20 s 内出现 → **RAM 启动机制本身可用** |
| 2 | header **v3**，同上 | fastboot 消失、设备保持运行、屏幕停在厂商标识 → **镜像被执行，UEFI 卡在内部** |
| 3 | v3 + SM8450 内存图 + FD `0xE5700000/6MB` + 栈 `0xA760D000` | 行为完全一样 |
| 4 | 加 `LogDxe`（写 `HAKIOS.LOG` 到 logfs） | 49 个镜像通过校验；启动后 **logfs 里没有文件** → 存储栈从未就绪/驱动未派发 |

结论：卡点在 **存储栈之前**（PrePi / DXE 核心 / 早期平台初始化），而这一层目前没有任何可读的输出。

## 可观测性的现状

| 通道 | 状态 |
|---|---|
| UART 串口 | 没有引出，需拆机 |
| `logfs`（UEFI 日志 FAT12 分区） | 已加驱动，但 UEFI 没走到能写它的地方 |
| `logdump`（512 MB） | 全 0，ABL 不写 |
| `pstore` / `ramoops` | 空 |
| `/dev/mem`（root 读物理内存） | Android 内核没有这个设备 |
| 屏幕 | 只能看到「厂商标识有没有变」 |
